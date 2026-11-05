from __future__ import annotations

import heapq

from .core_api import CoreAPI, RoutingCore
from .model import ControlMessage, INFINITY, Route


class LSCore(RoutingCore):
    """Maintain one router's local link-state routing information.

    An ``LSCore`` instance represents a single router.  It learns about its
    directly connected links from local events and learns about the rest of
    the topology from LSAs.  It does not inspect a global topology.  Instead,
    it stores the newest accepted LSA from each origin, constructs a consistent
    graph from that database, and computes routes to the prefixes owned by
    reachable LSA origins.

    EDIT THIS FILE. You may use heapq, but not a graph/routing library.

    Complete the six numbered student tasks in this order:

    1. Implement :meth:`_flood`.
    2. Implement :meth:`_originate`.
    3. Construct the consistent graph in :meth:`_recompute_routes`.
    4. Complete the Dijkstra loop in :meth:`_recompute_routes`.
    5. Implement :meth:`on_link_change`.
    6. Implement :meth:`on_control`.

    Attributes:
        router_id: This router's identifier, such as ``"R1"``.  It is also the
            origin key for this router's own entry in :attr:`lsdb`.
        own_prefix: Stub-network prefix owned and advertised by this router.
            Its local route always has metric zero and ``None'' as the next hop.
        neighbors: Mapping from each currently active, directly connected
            neighbor's router ID to the local link cost.  Each cost is an
            integer satisfying ``1 <= cost < INFINITY``.  This is authoritative
            local adjacency state, not a copy of another router's LSA.
        own_seq: Sequence number of the most recently originated self-LSA.
            Increment it whenever a fresh self-LSA is originated so receivers
            can distinguish the new LSA from stale or duplicate copies.
        lsdb: Link-state database keyed by LSA origin router ID.  Each value is
            a dictionary with exactly the protocol fields as in the example
            shown below::

                {
                    "seq": 7,
                    "prefix": "10.1.0.0/24",
                    "links": {"R2": 1, "R3": 4},
                }

            ``"seq"`` is that origin's latest accepted sequence number,
            ``"prefix"`` is the stub prefix owned by the origin, and
            ``"links"`` maps neighbor router IDs to link costs advertised by
            the origin.  An advertised link is not automatically usable:
            route computation requires matching advertisements from both
            endpoints with the same cost.
        routes: Current routing table keyed by destination prefix.  Values are
            :class:`Route` objects containing the total path metric and first-
            hop router ID.  The table always starts with ``own_prefix`` mapped
            to ``Route(0, None)``; remote prefixes are derived from reachable
            origins in ``lsdb``.
        _api: Staff-supplied :class:`CoreAPI` transport stored by the base
            :class:`RoutingCore`.
    """

    PERIOD_SECONDS = 5.0

    def __init__(self, router_id: str, own_prefix: str, api: CoreAPI):
        super().__init__(router_id, own_prefix, api)
        self.neighbors: dict[str, int] = {}
        self.own_seq = 0
        self.lsdb: dict[str, dict] = {
            router_id: {"seq": 0, "prefix": own_prefix, "links": {}}
        }
        self.routes: dict[str, Route] = {own_prefix: Route(0, None)}

    def _lsa_message(self, origin: str, entry: dict) -> ControlMessage:
        """Build an LS control message from one LSDB entry.

        The resulting message identifies the LSA's original router and carries
        the entry's sequence number, owned prefix, and advertised links.  The
        links dictionary is copied so that later mutation of the LSDB entry
        does not mutate the already constructed message.

        Args:
            origin: Router ID that originally created the LSA.  Note that
                this need not be this router's own ID when forwarding a
                learned LSA.
            entry: LSDB entry containing ``"seq"``, ``"prefix"``, and
                ``"links"`` fields.

        Returns:
            A :class:`ControlMessage` with protocol ``"LS"`` and payload type
            ``"lsa"``.
        """
        return ControlMessage(
            "LS",
            {
                "type": "lsa",
                "origin": origin,
                "seq": int(entry["seq"]),
                "prefix": entry["prefix"],
                "links": dict(entry["links"]),
            },
        )

    def _send_lsa(self, neighbor: str, origin: str, entry: dict) -> None:
        """Send one LSDB entry to an active directly connected neighbor.

        If ``neighbor`` is no longer present in :attr:`neighbors`, do nothing.
        Otherwise, convert ``entry`` with :meth:`_lsa_message` and send the
        resulting control message through the staff-provided transport.

        Args:
            neighbor: Router ID of the intended one-hop recipient.
            origin: Router ID that originally created the LSA.
            entry: LSA contents to send without changing their meaning.
        """
        if neighbor in self.neighbors:
            self.send_control(neighbor, self._lsa_message(origin, entry))

    def _flood(self, origin: str, entry: dict, exclude: str | None = None) -> None:
            """Flood an unchanged LSA to active neighbors other than ``exclude``.
    
            Send the LSA to every router ID currently present in
            :attr:`neighbors`, except the router whose ID equals ``exclude``.  The
            excluded router is normally the neighbor from which this copy arrived;
            omitting it avoids immediately reflecting the LSA back over the same
            link.  If ``exclude`` is ``None`` (or is not an active neighbor), send
            to all active neighbors.
    
            Flooding forwards an existing LSA rather than originating a new one.
            Pass the same ``origin`` and logically unchanged ``entry`` to every
            recipient.  In particular, do not increment its sequence number,
            replace its prefix, edit its links, or mutate the corresponding LSDB
            entry.  Iterating through neighbor IDs in sorted order makes sends
            deterministic, although the order does not change protocol semantics.
    
            Here ``R2`` forwards an LSA originated by ``R7`` to all of its active
            neighbors except the incoming neighbor ``R1``:
    
            >>> r2 = LSCore("R2", "10.2.0.0/24", None)
            >>> r2.neighbors = {"R4": 2, "R1": 1, "R3": 4}
            >>> entry = {
            ...     "seq": 8,
            ...     "prefix": "10.7.0.0/24",
            ...     "links": {"R6": 1, "R8": 3},
            ... }
            >>> sent = []
            >>> r2._send_lsa = lambda neighbor, origin, forwarded: sent.append(
            ...     (neighbor, origin, forwarded)
            ... )
            >>> r2._flood("R7", entry, exclude="R1")
            >>> [(neighbor, origin) for neighbor, origin, _ in sent]
            [('R3', 'R7'), ('R4', 'R7')]
            >>> all(forwarded == entry for _, _, forwarded in sent)
            True
            >>> entry
            {'seq': 8, 'prefix': '10.7.0.0/24', 'links': {'R6': 1, 'R8': 3}}
    
            With no exclusion, all three active neighbors receive the LSA:
    
            >>> sent.clear()
            >>> r2._flood("R7", entry)
            >>> [neighbor for neighbor, _, _ in sent]
            ['R1', 'R3', 'R4']
    
            Hint:
                Iterate over the keys of :attr:`neighbors`, skip the key equal to
                ``exclude``, and use the provided :meth:`_send_lsa` helper for each
                remaining neighbor.  That helper constructs and sends the LS
                control message, so ``_flood`` does not need to duplicate message-
                building logic.
    
            Args:
                origin: Router ID that originally created the LSA.
                entry: Accepted LSA contents to forward unchanged.
                exclude: Optional neighbor that must not receive this flooded copy.
            """
            # TODO 1: Flood this LSA to every active neighbor except ``exclude``.
            pass
    
    def _originate(self) -> None:
        """Create, install locally, and flood a new LSA for this router.

        Firstly create anew LSA: every locally originated LSA must be newer
        than this router's previous one.  Increment :attr:`own_seq` first and
        use the new value as the entry's ``"seq"`` field; do not forget to update
        the attribute itself.
        The entry must also contain :attr:`own_prefix` and a snapshot of every
        currently active adjacency in :attr:`neighbors`.  Copying the neighbor
        mapping prevents later link changes from mutating this LSA.  Building
        the copied links in sorted neighbor-ID order makes the stored state and
        serialized messages deterministic.

        Secondly, install it locally: Assigne the new entry to
        ``self.lsdb[self.router_id]``.  Replace only the LSDB entry whose origin
        is this router; entries learned from other origins must remain intact.
        Then, recompute so that route calculation sees the new local state.

        Finally, flood that same entry with ``self.router_id`` as its origin
        and with no excluded neighbor.

        This example starts at sequence number 4 and retains an unrelated LSA
        while replacing ``R1``'s own entry:

        >>> r1 = LSCore("R1", "10.1.0.0/24", None)
        >>> r1.own_seq = 4
        >>> r1.neighbors = {"R3": 4, "R2": 1}
        >>> r1.lsdb["R9"] = {
        ...     "seq": 2,
        ...     "prefix": "10.9.0.0/24",
        ...     "links": {},
        ... }
        >>> r1._originate()
        >>> r1.own_seq
        5
        >>> r1.lsdb["R1"]
        {'seq': 5, 'prefix': '10.1.0.0/24', 'links': {'R2': 1, 'R3': 4}}
        >>> "R9" in r1.lsdb
        True

        Calling the method again creates a fresh self-LSA even if the
        adjacency set has not changed:

        >>> r1._originate()
        >>> r1.own_seq == r1.lsdb["R1"]["seq"] == 6
        True
        """
        # TODO 2: Create, install, recompute for, and flood a new self-LSA.
        pass

    def _recompute_routes(self) -> None:
        """Rebuild prefix routes from the current link-state database.

        This method has three stages.  The first two are numbered student
        tasks; the third is provided.

        **1. Construct a consistent router graph.**

        The vertices are router IDs found either as origins in :attr:`lsdb` or
        as neighbors in an LSA's ``"links"`` mapping.  An advertised link
        ``A-B`` is usable only when the current LSAs for both ``A`` and ``B``
        exist and advertise one another with exactly the same cost.  Add every
        such usable link in both directions.  This reciprocal check prevents
        routing over a stale half-link while new LSAs are propagating.

        **2. Find shortest paths between routers.**

        The provided setup initializes a heap with this router's immediate
        graph neighbors.  Each heap item is a tuple containing
        ``(distance, first_hop, complete_path, current_router)``.  Python
        compares tuples from left to right, which gives the required ordering:
        prefer lower total cost, then the lexicographically smaller first hop,
        and finally the lexicographically smaller complete router path.

        Complete the loop by discarding an entry when ``best`` already
        contains an equal or better key for that router; otherwise accept the
        entry, install ``Route(distance, first_hop)`` in ``router_routes``, and
        push paths extended through each adjacent router not already present
        in ``complete_path``.  Keeping routers out of their own path prevents
        cycles.

        **3. Translate router paths into prefix routes.**

        Dijkstra produces routes to router IDs, whereas the public routing
        table is keyed by the prefixes advertised in LSAs.  Begin the new table
        with :attr:`own_prefix` at metric zero.  For every other LSDB origin
        reachable in ``router_routes``, associate that origin's advertised
        prefix with the corresponding :class:`Route`.  Omit unreachable
        origins, then replace :attr:`routes` with the completed new table so
        stale prefix routes disappear. **This stage is already implemented
        and students must not change it.**

        This method mutates :attr:`routes` and returns ``None``.
        """
        # Stage 1 (provided setup): include LSDB origins and routers mentioned
        # by their LSAs, even when some of those vertices are currently
        # isolated.  Students complete only the reciprocal-edge construction.
        nodes = set(self.lsdb)
        for entry in self.lsdb.values():
            nodes.update(entry["links"])

        # ``graph`` is supposed to hold an adjacency mapping of the form
        # ``router_id -> {neighbor_id: link_cost}``.  Each usable undirected
        # link appears in both endpoint mappings.  For example, a graph
        # of three routers R1, R2, and R3 with links R1-R2 with cost 1
        # and R1-R3 with cost 4 is represented with the following ``graph'':
        # {"R1": {"R2": 1, "R3": 4},
        #  "R2": {"R1": 1},
        #  "R3": {"R1": 4}}
        graph: dict[str, dict[str, int]] = {node: {} for node in nodes}

        # TODO 3 (_recompute_routes Stage 1): Add an undirected A-B edge only
        # when the current LSAs for A and B advertise one another with the same
        # cost.

        # Stage 2 (provided setup): a route to this router has cost zero and no
        # next hop.  Seed the heap with paths to its immediate graph neighbors.
        router_routes: dict[str, Route] = {self.router_id: Route(0, None)}
        heap: list[tuple[int, str, tuple[str, ...], str]] = []
        for neighbor, cost in graph.get(self.router_id, {}).items():
            heapq.heappush(
                heap,
                (
                    cost,  # distance to the destination
                    neighbor,  # next hop
                    (self.router_id, neighbor),  # entire path to the destination
                    neighbor,  # destination
                ),
            )

        # ``best`` records the best accepted path-ranking key for each reached
        # router: router ID -> (distance, first hop, complete router path).
        # For example, {"R4": (5, "R2", ("R1", "R2", "R4"))} means that the
        # accepted route to R4 costs 5 and starts through R2.
        best: dict[str, tuple[int, str, tuple[str, ...]]] = {}

        while heap:
            distance, first_hop, complete_path, current_router = heapq.heappop(heap)
            candidate = (distance, first_hop, complete_path)

            # TODO 4 (_recompute_routes Stage 2): Ignore an equal/worse
            # candidate already in ``best``.  Otherwise accept it, update
            # ``router_routes``, and push every cycle-free one-link extension
            # onto ``heap``.

        # Stage 3 (provided entirely): For every remote LSDB origin reachable
        # according to ``router_routes``, map its advertised prefix to its
        # router route.
        routes: dict[str, Route] = {self.own_prefix: Route(0, None)}
        for origin, entry in self.lsdb.items():
            if origin == self.router_id:
                continue
            rr = router_routes.get(origin)
            if rr is not None:
                routes[entry["prefix"]] = rr
        self.routes = routes

    def on_link_change(self, neighbor: str, cost: int | None) -> None:
        """Process a local adjacency change and advertise the new local state.

        ``cost`` is either ``None`` or an integer satisfying
        ``1 <= cost < INFINITY``.  ``None`` means that the link is down or has
        been disconnected.  Remove ``neighbor`` from :attr:`neighbors` if it
        is present, then call :meth:`_originate` so the router installs and
        floods a newer self-LSA without that adjacency.  Do not delete the
        neighbor's own entry from :attr:`lsdb`: an LSDB contains the newest LSA
        known for each origin, whereas ``neighbors`` contains current local
        adjacency state.  Reciprocal-link validation during route computation
        prevents the retained remote LSA from keeping the failed link usable.

        A non-``None`` cost represents a link-up event, a newly discovered
        neighbor, or an administrative cost change.  Ignore a cost outside the
        valid range without changing state or originating an LSA.  For a valid
        cost, determine whether the neighbor is new *before* inserting or
        updating it in ``neighbors``.  Then originate a new self-LSA so it
        contains the current cost.

        A newly connected neighbor may not yet possess the rest of this
        router's LSDB.  After origination has updated
        ``self.lsdb[self.router_id]``, send every current LSDB entry to that new
        neighbor with :meth:`_send_lsa`, iterating through origins in sorted
        order for deterministic behavior.  This full synchronization is only
        needed for a new neighbor; an existing neighbor whose cost changes
        receives the new self-LSA through normal flooding.

        Args:
            neighbor: Router ID at the other endpoint of the local link.
            cost: New positive link cost strictly below :data:`INFINITY`, or
                ``None`` when the link is down.
        """
        # TODO 5: Process the link event, originate, and synchronize if needed.
        pass

    def on_control(self, src: str, message: ControlMessage) -> None:
        """Validate and process an LSA received from one active neighbor.

        Silently discard a message unless ``src`` is currently present in
        :attr:`neighbors` and ``message.protocol`` is exactly ``"LS"``.  A
        valid LSA payload must satisfy all of the following requirements:

        * ``"type"`` is exactly ``"lsa"``;
        * ``"origin"`` and ``"prefix"`` are strings, and the prefix contains
          the ``/`` prefix-length separator;
        * ``"seq"`` is a non-negative integer, but not a boolean; and
        * ``"links"`` is a dictionary in which every neighbor ID is a string
          and every cost is a non-boolean integer satisfying
          ``1 <= cost < INFINITY``.

        Unlike DV entry filtering, one malformed link mapping invalidates the
        whole LSA.  Invalid messages must not modify the LSDB, recompute routes,
        or trigger flooding.

        Handle a valid LSA claiming this router as its ``origin`` specially.
        There are two possible cases:
        1) If its sequence number is no greater than :attr:`own_seq`, simply ignore
        it as its probably your own LSA that you received back through normal
        flooding.
        2) If its sequence is greater than :attr:`own_seq`, perform
        *self-LSA fight-back*: first advance ``own_seq`` to the received sequence
        value, then call :meth:`_originate`. Origination increments the counter
        once more and floods this router's correct prefix and current local links
        with a strictly newer sequence number.
        Never install another router's version of this router's own LSA.

        For an LSA originated by another router, compare its sequence number
        with the current entry for that same origin in :attr:`lsdb`.  Ignore a
        duplicate or stale LSA whose sequence number is less than or equal to
        the stored value.  Otherwise, construct a fresh entry containing the
        received sequence number and prefix plus a copied, deterministically
        sorted links mapping, and replace ``self.lsdb[origin]`` with it.
        Recompute routes after installing the newer entry, then flood that
        entry unchanged to every active neighbor except ``src``.  Excluding the
        incoming neighbor avoids immediately sending the LSA back over the
        link on which it arrived.

        Args:
            src: Router ID of the directly connected neighbor that delivered
                the message.
            message: Candidate LS control message to validate and process.
        """
        # TODO 6: Validate and process this received LSA.
        pass

    def on_periodic(self) -> None:
        """Refresh the router's own LSA."""
        self._originate()

    def get_route(self, prefix: str) -> Route | None:
        if prefix == self.own_prefix:
            return Route(0, None)
        route = self.routes.get(prefix)
        if route is None or route.metric >= INFINITY or route.next_hop is None:
            return None
        return route

    def all_routes(self) -> dict[str, Route]:
        return {
            p: r
            for p, r in self.routes.items()
            if p != self.own_prefix and r.metric < INFINITY and r.next_hop is not None
        }

    def debug_state(self) -> str:
        return f"seq={self.own_seq}; LSDB={sorted(self.lsdb)}; routes=" + "; ".join(
            f"{p}={r.metric} via {r.next_hop}"
            for p, r in sorted(self.all_routes().items())
        )

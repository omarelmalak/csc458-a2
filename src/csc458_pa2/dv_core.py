from __future__ import annotations

from .core_api import CoreAPI, RoutingCore
from .model import ControlMessage, INFINITY, Route


class DVCore(RoutingCore):
    """Maintain one router's local distance-vector routing state.

    A ``DVCore`` instance represents a single router.  It learns only from
    local link events and control messages sent by directly connected
    neighbors; it has no access to the global topology.  The supplied runtime
    calls the event handlers, while this class maintains the received vectors,
    computes routes with Bellman--Ford, and sends neighbor-specific
    advertisements through the inherited :meth:`send_control` method.

    EDIT THIS FILE. You may add helpers and private state, but keep the public
    method signatures unchanged. Do not import Mininet or inspect global
    topology files from this module.

    Complete the four numbered student tasks in this order:

    1. Implement :meth:`_advertisement_for`.
    2. Implement :meth:`_recompute_routes`.
    3. Implement :meth:`on_link_change`.
    4. Implement :meth:`on_control`.

    Attributes:
        PERIOD_SECONDS: Number of seconds between calls to
            :meth:`on_periodic` by the supplied runtime.
        router_id: This router's identifier, such as ``"R1"``.  This attribute
            is initialized by :class:`RoutingCore`.
        own_prefix: Stub-network prefix originated by this router.  It must
            always have local metric zero and no next hop.
        mode: Outgoing-advertisement policy.  Its value is ``"basic"``,
            ``"split_horizon"``, or ``"poison_reverse"``.  The mode affects
            advertisements but not the Bellman--Ford recurrence itself.
        neighbors: Mapping from each currently active, directly connected
            neighbor's router ID to the local cost of that link.  Every stored
            cost is an integer satisfying ``1 <= cost < INFINITY``.
        neighbor_vectors: Mapping from a neighbor router ID to that neighbor's
            most recently accepted, sanitized full distance vector.  Each
            inner dictionary maps destination prefixes to metrics capped at
            :data:`INFINITY`.  A new neighbor may have an empty vector until
            its first valid advertisement arrives.
        known_prefixes: Set of this router's own prefix and every valid prefix
            learned from accepted advertisements.  Prefixes remain known even
            when no neighbor currently offers a usable route to them.
        routes: Current routing table, mapping every known prefix to a
            :class:`Route`.  Unreachable destinations may remain in the table
            with metric ``INFINITY`` and next hop ``None``; public route-query
            methods filter those entries as appropriate.
        _api: Staff-supplied :class:`CoreAPI` transport retained by
            :class:`RoutingCore`.  Student code should normally communicate
            through :meth:`send_control` instead of accessing it directly.
    """

    PERIOD_SECONDS = 2.0

    def __init__(
        self,
        router_id: str,
        own_prefix: str,
        api: CoreAPI,
        mode: str = "poison_reverse",
    ):
        super().__init__(router_id, own_prefix, api)
        if mode not in {"basic", "split_horizon", "poison_reverse"}:
            raise ValueError("invalid DV mode")
        self.mode = mode
        self.neighbors: dict[str, int] = {}
        self.neighbor_vectors: dict[str, dict[str, int]] = {}
        self.known_prefixes: set[str] = {own_prefix}
        self.routes: dict[str, Route] = {own_prefix: Route(0, None)}

    def _advertisement_for(self, neighbor: str) -> dict[str, int]:
            """Build the full distance vector to send to ``neighbor``.
    
            ``neighbor`` is a router ID, not an IP prefix.  The returned dictionary
            maps every advertised prefix to this router's current metric for that
            prefix.  Include prefixes remembered in :attr:`known_prefixes` as well
            as prefixes currently present in :attr:`routes`; a remembered prefix
            without a route is unreachable and must therefore be advertised with
            :data:`INFINITY`.  Never advertise a metric greater than
            :data:`INFINITY`.
    
            Be especially mindful of :attr:`mode`.  Do not assume that the
            constructor's default mode is in use: tests may change ``self.mode`` or
            construct a core in any of the three supported modes.
    
            For a *remote* route whose ``next_hop`` is the receiving ``neighbor``:
    
            * ``"basic"`` advertises the route's current (capped) metric;
            * ``"split_horizon"`` omits the prefix from this neighbor's vector;
            * ``"poison_reverse"`` includes the prefix with metric ``INFINITY``.
    
            Routes using a different next hop are advertised normally.  The
            router's own prefix is the exception to all filtering rules and must
            always be present with metric zero.  Return a new dictionary; do not
            mutate :attr:`routes` or :attr:`known_prefixes` while preparing a
            neighbor-specific advertisement.
    
            The following example uses one route learned through ``R2``.  Notice
            how changing only ``mode`` changes the advertisement sent to ``R2``:
    
            >>> r1 = DVCore("R1", "10.1.0.0/24", None)
            >>> r1.known_prefixes.add("10.4.0.0/24")
            >>> r1.routes["10.4.0.0/24"] = Route(3, "R2")
            >>> r1.mode = "basic"
            >>> r1._advertisement_for("R2")
            {'10.1.0.0/24': 0, '10.4.0.0/24': 3}
            >>> r1.mode = "split_horizon"
            >>> r1._advertisement_for("R2")
            {'10.1.0.0/24': 0}
            >>> r1.mode = "poison_reverse"
            >>> r1._advertisement_for("R2")
            {'10.1.0.0/24': 0, '10.4.0.0/24': 16}
    
            Hint:
                Consider each prefix in the union of the remembered prefixes and
                routing-table keys.  Use an unreachable placeholder for a prefix
                that has no current route, then apply the selected mode only when
                the route's next hop equals ``neighbor``.  Iterating in sorted
                prefix order makes the resulting vector deterministic.
    
            Args:
                neighbor: ID of the directly connected router that will receive
                    this advertisement.
    
            Returns:
                A newly allocated prefix-to-metric dictionary tailored to
                ``neighbor``.
            """
            all_prefixes = set()

            for prefix in self.known_prefixes:
                all_prefixes.add(prefix)

            for prefix in self.routes:
                all_prefixes.add(prefix)
  
            advertisement = {}
            for prefix in all_prefixes:
                if prefix not in self.routes:
                    advertisement[prefix] = INFINITY
                else:
                    distance = self.routes[prefix].metric
                    next_hop = self.routes[prefix].next_hop

                    if self.mode == "split_horizon" and next_hop == neighbor:
                        continue
                    elif self.mode == "poison_reverse" and next_hop == neighbor:
                        advertisement[prefix] = INFINITY
                        continue
                    
                    advertisement[prefix] = distance

            return advertisement
    
    def _recompute_routes(self) -> bool:
        """Rebuild this router's table with the Bellman-Ford recurrence.

        Use only the information locally available to a distance-vector
        router: the link costs in :attr:`neighbors` and the most recently
        received advertisements in :attr:`neighbor_vectors`.  For a
        destination ``d`` advertised by a neighbor ``n``, the candidate path
        has cost ``cost_to_n + advertised_cost_to_d``.  Cap every candidate at
        :data:`INFINITY` before comparing it with the alternatives.

        Recompute routes for every prefix already in :attr:`known_prefixes`
        and every prefix appearing in any stored neighbor vector.  Newly seen
        prefixes must also be added to ``known_prefixes`` so that they remain
        known if a later advertisement omits them.  A known destination with
        no usable candidate is retained as ``Route(INFINITY, None)``.  The
        router's own prefix is always installed as ``Route(0, None)``.

        If two neighbors offer the same minimum metric, choose the
        lexicographically smaller router ID as the next hop, regardless of
        dictionary insertion order.  An infinite route has no next hop, even
        if one or more neighbors advertised it.  Note that :attr:`mode` does
        not affect this calculation: basic DV, split horizon, and poison
        reverse change outgoing advertisements, not the local Bellman-Ford
        rule.

        Replace :attr:`routes` with the newly computed table and report whether
        its contents differ from the previous table.  Thus, receiving an
        update does not necessarily mean this method should return ``True``.

        In this example, both neighbors offer an equal-cost route to
        ``10.4.0.0/24``.  ``R2`` wins the tie even though ``R3`` was inserted
        first.  The other advertised route reaches the assignment's infinity:

        >>> r1 = DVCore("R1", "10.1.0.0/24", None)
        >>> r1.neighbors = {"R3": 1, "R2": 1}
        >>> r1.neighbor_vectors = {
        ...     "R3": {"10.4.0.0/24": 2},
        ...     "R2": {"10.4.0.0/24": 2, "10.5.0.0/24": 15},
        ... }
        >>> r1._recompute_routes()
        True
        >>> r1.routes["10.4.0.0/24"]
        Route(metric=3, next_hop='R2')
        >>> r1.routes["10.5.0.0/24"] == Route(INFINITY, None)
        True
        >>> "10.5.0.0/24" in r1.known_prefixes
        True
        >>> r1._recompute_routes()  # No input has changed.
        False

        Hint:
            Save a shallow copy of the old routing table before building a new
            one.  Gather the destination set first, then consider each active
            neighbor that actually advertised the destination.  Candidate
            pairs of ``(capped_metric, neighbor_id)`` make the required
            metric-first, router-ID-second tie-break convenient.  After
            handling the no-candidate and infinite-metric cases, install the
            new table and compare it with the saved copy.

        Returns:
            ``True`` exactly when the newly computed routing table differs
            from the old table; otherwise ``False``.
        """
        new_routing_table = {}
        for prefix in self.routes:
            distance = self.routes[prefix].metric
            next_hop = self.routes[prefix].next_hop
            if distance == 0 and next_hop is None:
                new_routing_table[prefix] = Route(0, None)

        for neighbor in self.neighbor_vectors:
            advertisements = self.neighbor_vectors[neighbor]
            for prefix in advertisements:
                if prefix not in self.known_prefixes:
                    self.known_prefixes.add(prefix)

        change_made = False
        for prefix in self.known_prefixes:
            # Own prefix case (already added at the beginning of function)
            if prefix in new_routing_table:
                continue

            route = self._find_minimum_route_for_prefix(prefix)
             
            new_routing_table[prefix] = route

            if prefix not in self.routes:
                change_made = True
                continue

            if route.metric != self.routes[prefix].metric or route.next_hop != self.routes[prefix].next_hop:
                change_made = True

        self.routes = new_routing_table
        return change_made

    
    def _find_minimum_route_for_prefix(self, prefix) -> Route:
        # Return format example: Route(2, "R3")
        min_distance = INFINITY
        min_neighbor = None

        min_route = (min_distance, min_neighbor)

        for neighbor in self.neighbor_vectors:
            advertisements = self.neighbor_vectors[neighbor]
            if prefix in advertisements:
                advertised_distance_vector = advertisements[prefix]
                local_distance = self.neighbors[neighbor]

                total_distance = advertised_distance_vector + local_distance

                if total_distance >= INFINITY:
                    continue

                curr_route = (total_distance, neighbor)
                
                if curr_route < min_route:
                    min_route = curr_route
        
        return Route(min_route[0], min_route[1])


    def _send_updates(self, only: str | None = None) -> None:
        """Send a full DV to every active neighbor, or only one neighbor."""
        targets = [only] if only else sorted(self.neighbors)
        for n in targets:
            if n not in self.neighbors:
                continue
            self.send_control(
                n,
                ControlMessage(
                    "DV", {"type": "dv", "vector": self._advertisement_for(n)}
                ),
            )

    def on_link_change(self, neighbor: str, cost: int | None) -> None:
        """Process a change to one directly connected link.

        ``cost`` is either ``None`` or an integer satisfying
        ``1 <= cost < INFINITY``.  ``None`` means that the link is down or has
        been disconnected.  In that case, remove ``neighbor`` from
        :attr:`neighbors` and discard its advertised vector from
        :attr:`neighbor_vectors`.  Both removals should tolerate an already
        absent neighbor.  Discarding the vector is important: routes must not
        continue to use information learned over a failed link.

        A non-``None`` cost means that the link is up, newly added, or has a
        new administrative cost.  Reject a cost outside the valid range
        without changing state or sending an update.  For a valid cost, store
        it in ``neighbors`` and ensure that ``neighbor_vectors`` contains an
        entry for the neighbor.  Create an empty vector for a new neighbor, but
        preserve an existing vector when only the link cost changes.

        After either a valid up/change event or a down event, recompute the
        entire local routing table.  If the table changed, send one update to
        all currently active neighbors.  If the table did not change
        and ``cost`` is non-``None``, send an update only to the affected
        neighbor.  Why do you think we need to do this?

        A link-down event never sends directly to the removed neighbor.  It
        broadcasts to the remaining neighbors if the table changed and sends
        nothing if the table did not change.

        The first example shows that bringing up a link sends to that neighbor
        even when ``_recompute_routes`` reports no routing-table change:

        >>> r1 = DVCore("R1", "10.1.0.0/24", None)
        >>> sends = []
        >>> r1._recompute_routes = lambda: False
        >>> r1._send_updates = lambda only=None: sends.append(only)
        >>> r1.on_link_change("R2", 3)
        >>> r1.neighbors
        {'R2': 3}
        >>> r1.neighbor_vectors
        {'R2': {}}
        >>> sends
        ['R2']

        If a later cost change alters the table, one broadcast is sufficient
        because ``R2`` is now an active neighbor.  Here ``None`` in ``sends``
        represents calling ``_send_updates()`` without an ``only`` argument:

        >>> r1.neighbor_vectors["R2"] = {"10.4.0.0/24": 4}
        >>> r1._recompute_routes = lambda: True
        >>> sends.clear()
        >>> r1.on_link_change("R2", 5)
        >>> r1.neighbor_vectors["R2"]  # The previously received DV remains.
        {'10.4.0.0/24': 4}
        >>> sends
        [None]
        >>> sends.clear()
        >>> r1.on_link_change("R2", None)
        >>> "R2" in r1.neighbors or "R2" in r1.neighbor_vectors
        False
        >>> sends
        [None]


        Args:
            neighbor: Router ID of the directly connected neighbor whose link
                changed.
            cost: New positive link cost strictly below :data:`INFINITY`,
                or ``None`` when the link is down.
        """
        # TODO 3: Implement on_link_change.
        pass

    def on_control(self, src: str, message: ControlMessage) -> None:
        """Validate and process a distance vector received from ``src``.

        Accept control traffic only from a router currently present in
        :attr:`neighbors`.  Silently discard a message from any other source,
        even if the message itself is well formed.  Also discard the *entire*
        message, without changing state, recomputing routes, or sending an
        update, if any of these envelope checks fails:

        * ``message.protocol`` is not exactly ``"DV"``;
        * ``message.payload["type"]`` is not exactly ``"dv"``; or
        * ``message.payload["vector"]`` is not a dictionary.

        Validate the entries of an otherwise acceptable vector individually.
        A malformed prefix or metric invalidates only that prefix-to-metric
        mapping, not the rest of the advertisement.  At minimum, reject a
        prefix key that is not a string or does not contain the ``/`` prefix-
        length separator.  Metrics must be non-negative integers; in
        particular, booleans, negative integers, strings, and floating-point
        values are not valid metrics.  Cap an accepted metric greater than
        :data:`INFINITY` at ``INFINITY``.

        Update the previous entry for ``src`` in :attr:`neighbor_vectors`.
        Note that the received dictionary is a full vector, rather than an
        incremental patch.

        Don't forget to update :attr:`known_prefixes` if needed.

        Recompute the local routes. Send update to all active neighbors,
        if needed.


        >>> r1 = DVCore("R1", "10.1.0.0/24", None)
        >>> r1.neighbors = {"R2": 1}
        >>> r1.neighbor_vectors = {"R2": {"10.9.0.0/24": 2}}
        >>> good = ControlMessage(
        ...     "DV", {"type": "dv", "vector": {"10.3.0.0/24": 2}}
        ... )
        >>> r1.on_control("R9", good)  # R9 is not a current neighbor.
        >>> malformed = (
        ...     ControlMessage("LS", {"type": "dv", "vector": {}}),
        ...     ControlMessage("DV", {"type": "lsa", "vector": {}}),
        ...     ControlMessage("DV", {"type": "dv", "vector": []}),
        ... )
        >>> for bad_message in malformed:
        ...     r1.on_control("R2", bad_message)
        >>> r1.neighbor_vectors
        {'R2': {'10.9.0.0/24': 2}}


        Within a valid message, bad mappings are ignored while good mappings
        are installed.  The old ``R2`` vector is replaced, the large metric is
        capped, and a changed routing table causes one all-neighbor update.

        >>> advertised = {
        ...     "10.3.0.0/24": 2,
        ...     "missing-prefix-length": 4,
        ...     7: 3,
        ...     "10.4.0.0/24": -1,
        ...     "10.5.0.0/24": True,
        ...     "10.6.0.0/24": 99,
        ... }
        >>> r1.on_control(
        ...     "R2", ControlMessage("DV", {"type": "dv", "vector": advertised})
        ... )
        >>> r1.neighbor_vectors["R2"]
        {'10.3.0.0/24': 2, '10.6.0.0/24': 16}
        >>> {"10.3.0.0/24", "10.6.0.0/24"} <= r1.known_prefixes
        True


        Args:
            src: Router ID from which the control message was received.
            message: Candidate DV control message to validate and process.
        """
        # TODO 4: Implement on_control.
        pass

    def on_periodic(self) -> None:
        """Send a periodic full-vector refresh."""
        self._send_updates()

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
        return "; ".join(
            f"{p}={r.metric} via {r.next_hop}" if r.metric < INFINITY else f"{p}=INF"
            for p, r in sorted(self.routes.items())
            if p != self.own_prefix
        )

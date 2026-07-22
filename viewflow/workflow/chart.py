# coding: utf-8
from __future__ import division

import math
import re
from copy import copy
from itertools import groupby
from textwrap import wrap

from django.template.loader import get_template
from django.utils.encoding import force_str
from .status import STATUS

GAP_SIZE = 25
EDGE_START_GAP_SIZE = 2
EDGE_END_GAP_SIZE = 7

DEFAULT_SHAPE = {
    "width": 150,
    "height": 100,
    "svg": """
        <rect class="task" width="150" height="100" rx="5" ry="5"/>
    """,
}


class Edge(object):
    __slots__ = ["src", "dst", "segments", "label", "label_pos", "edge_class"]

    def __init__(self, src, dst, segments=None, label=None, edge_class=None):
        self.src = src
        self.dst = dst
        self.segments = segments if segments is not None else []
        self.label = label
        self.label_pos = None
        self.edge_class = edge_class


class Shape(object):
    __slots__ = ["x", "y", "width", "height", "svg", "text"]

    def __init__(self, x=-1, y=-1, width=-1, height=-1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = []

    def label(self):
        return " ".join(segment[0] for segment in self.text)


class Cell(object):
    __slots__ = [
        "col",
        "row",
        "x",
        "y",
        "width",
        "height",
        "node",
        "shape",
        "title",
        "status",
    ]

    def __init__(
        self,
        node,
        col=-1,
        row=-1,
        x=-1,
        y=-1,
        width=-1,
        height=-1,
        shape=None,
        title=None,
        status=None,
    ):
        self.node = node
        self.col = col
        self.row = row
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape if shape is not None else Shape()
        self.title = title
        self.status = status

    def incoming(self):
        return self.node._incoming()

    def outgoing(self):
        return self.node._outgoing()


class Grid(object):
    def __init__(self, nodes):
        self.width = -1
        self.height = -1
        self.flow_class = None

        self.grid = {node: Cell(node) for node in nodes}
        self.edges = [
            Edge(edge.src, edge.dst, label=edge.label, edge_class=edge.edge_class)
            for node in nodes
            for edge in node._incoming()
        ]

    def __getitem__(self, node):
        return self.grid[node]

    @property
    def nodes(self):
        return self.grid.keys()

    @property
    def cells(self):
        return self.grid.values()

    def insert_row_below(self, row):
        for cell in self.cells:
            if cell.row != -1 and cell.row > row:
                cell.row += 1

    def insert_row_above(self, row):
        for cell in self.cells:
            if cell.row != -1 and cell.row >= row:
                cell.row += 1

    def place_start_node(self, node):
        """Place node on a new row in a first column."""
        cell = self[node]
        last_row = max(cell.row for cell in self.cells)
        cell.col, cell.row = 0, last_row + 1

    def place_next_to(self, prev, node):
        """Place node at the right of the previous node.

        If node have no row pre-initialized, the row of previous node is used
        """
        prev_cell, node_cell = self[prev], self[node]
        if node_cell.row == -1:
            node_cell.row = prev_cell.row
        node_cell.col = prev_cell.col + 1

    def distribute_children(self, parent, children):
        """Preinitialize children node rows to be equally spread over parent."""
        children = [child for child in children if self[child].row == -1]
        parent_cell = self[parent]
        half = len(children) / 2
        above = children[0 : int(math.floor(half))]
        middle = children[int(math.floor(half)) : int(math.ceil(half))]
        below = children[int(math.ceil(half)) :]
        for child in above:
            self.insert_row_above(parent_cell.row)
            self[child].row = parent_cell.row - 1
        for child in middle:
            self[child].row = parent_cell.row
        for child in reversed(below):
            self.insert_row_below(parent_cell.row)
            self[child].row = parent_cell.row + 1

    def place_boundary_below(self, host, node):
        """Place a boundary event's chain on a fresh row below its host.

        Boundary events dangle off the bottom of the host task, so their
        downstream path must not compete with the host's real "next" branch
        for the center row. Stacks multiple boundaries under one another.
        """
        host_cell, node_cell = self[host], self[node]
        # stack under the host and under any boundary siblings already placed,
        # so boundaries keep their declaration order top-to-bottom
        siblings = [
            self[other].row
            for other in self.nodes
            if getattr(other, "_attached_to", None) is host and self[other].row != -1
        ]
        base = max([host_cell.row] + siblings)
        self.insert_row_below(base)
        node_cell.row = base + 1
        node_cell.col = host_cell.col + 1

    def place_under_host(self, host, node):
        """Place a node in its boundary host's column, on a fresh row below.

        Keeps a lone boundary event's downstream target directly under the
        host so its edge drops straight down, clear of the host's forward
        branches.
        """
        host_cell, node_cell = self[host], self[node]
        below = [
            self[other].row
            for other in self.nodes
            if self[other].col == host_cell.col
            and self[other].row > host_cell.row
            and self[other].row != -1
        ]
        base = max([host_cell.row] + below)
        self.insert_row_below(base)
        node_cell.row = base + 1
        node_cell.col = host_cell.col

    def place_join(self, prev_split, prevs, node):
        """Place join after prev nodes on the same row as prev_split.

        If prev_split is None, center row of prev nodes used
        """
        node_cell = self[node]
        node_cell.col = max(self[prev].col for prev in prevs) + 1
        if prev_split:
            prev_split_cell = self[prev_split]
            node_cell.row = prev_split_cell.row
        else:
            if node_cell.row == -1:
                max_prev_row = max(self[prev].row for prev in prevs)
                min_prev_row = min(self[prev].row for prev in prevs)
                row = (max_prev_row - min_prev_row) / 2
                if row % 1 == 0:
                    node_cell.row = int(row)
                else:
                    self.insert_row_below(int(row))
                    node_cell.row = int(row) + 1

    def collapse_grid(self):
        """Remove empty rows and columns left behind by row insertions."""
        rows = sorted({cell.row for cell in self.cells})
        cols = sorted({cell.col for cell in self.cells})
        row_map = {row: index for index, row in enumerate(rows)}
        col_map = {col: index for index, col in enumerate(cols)}
        for cell in self.cells:
            cell.row = row_map[cell.row]
            cell.col = col_map[cell.col]

    def resolve_collisions(self):
        """Move each cell that shares a grid slot onto a fresh empty row."""
        while True:
            occupied = {}
            collision = None
            for cell in sorted(
                self.cells, key=lambda cell: (cell.row, cell.col, cell.node.name)
            ):
                key = (cell.row, cell.col)
                if key in occupied:
                    collision = cell
                    break
                occupied[key] = cell
            if collision is None:
                break
            self.insert_row_below(collision.row)
            collision.row += 1


def topsort(flow_class):
    result, incoming_to_reverse = [], {}

    nodes = list(flow_class.instance.nodes())
    incoming_edges = {node: {edge.src for edge in node._incoming()} for node in nodes}
    initial_incoming = {node: set(incoming_edges[node]) for node in nodes}

    while nodes:
        start_nodes, circle_broken = [], False
        for node in nodes:
            if not incoming_edges[node]:
                start_nodes.append(node)

        if start_nodes:
            for start_node in start_nodes:
                nodes.remove(start_node)
                result.append(start_node)
                for _, sources in incoming_edges.items():
                    sources.discard(start_node)
        else:
            # Fix edges
            for join in nodes:
                if len(incoming_edges[join]) < len(initial_incoming[join]):
                    incoming_to_reverse[join] = copy(incoming_edges[join])
                    for source in incoming_edges[join]:
                        incoming_edges[source].add(join)
                    incoming_edges[join] = set()
                    circle_broken = True
            if not circle_broken:
                node = nodes[0]  # TODO Grab node from a circle
                nodes.remove(node)
                result.append(node)
                for _, sources in incoming_edges.items():
                    sources.discard(node)

    return result, incoming_to_reverse


def find_prev_split(nodes, incoming_edges, outgoing_edges, join):
    """Find the split for join"""

    def is_split_node(source):
        return len(outgoing_edges[source]) > 1

    def is_join_node(source):
        return len(incoming_edges[source]) > 1

    def collect_splits(node, prev_nodes=None):
        """Breadth first split node list."""
        if prev_nodes is None:
            prev_nodes = []

        for source in incoming_edges[node]:
            if is_split_node(source):
                yield source
        for source in incoming_edges[node]:
            if source not in prev_nodes:
                for split in collect_splits(source, prev_nodes + [source]):
                    yield split

    incoming_splits = [
        [source] if is_split_node(source) else [] + list(collect_splits(source))
        for source in incoming_edges[join]
    ]
    if not incoming_splits:
        # No incoming edges
        return None

    common_splits = sorted(
        set.intersection(*[set(splits) for splits in incoming_splits]),
        key=lambda split: incoming_splits[0].index(split),
    )

    if not common_splits:
        return None

    return common_splits[0]


def layout(nodes, incoming_edges, outgoing_edges):
    grid = Grid(nodes)

    for node in nodes:
        incomings, outgoings = incoming_edges[node], outgoing_edges[node]
        placed_incomings = [
            incoming for incoming in incomings if grid[incoming].col != -1
        ]

        host = getattr(node, "_attached_to", None)
        prev = incomings[0] if len(placed_incomings) == 1 else None
        boundary_host = (
            getattr(prev, "_attached_to", None) if prev is not None else None
        )
        if host is not None and grid[host].col != -1:
            # boundary event: dangle its chain on a fresh row below the host
            grid.place_boundary_below(host, node)
        elif len(placed_incomings) == 0:
            grid.place_start_node(node)
        elif (
            boundary_host is not None
            and grid[boundary_host].col != -1
            and len(getattr(boundary_host, "_boundary_events", [])) == 1
        ):
            # first node downstream of a lone boundary event -- keep it in
            # the boundary's below-host lane so its edge drops straight down
            # instead of cutting across the host's own forward branches.
            # Skipped for multi-boundary hosts, where a shared lane would
            # make the chains cross each other instead.
            grid.place_under_host(boundary_host, node)
        elif len(placed_incomings) == 1:
            grid.place_next_to(incomings[0], node)
        else:
            prev_split = find_prev_split(nodes, incoming_edges, outgoing_edges, node)
            grid.place_join(prev_split, placed_incomings, node)

        if len(outgoings) > 1:
            for child in outgoings:
                if len(incoming_edges[child]) > 1:
                    if node in incoming_edges[child]:
                        # join connected directly to split
                        outgoings = copy(outgoings)
                        outgoings.remove(child)
                        outgoings = (
                            outgoings[0 : int(len(outgoings) / 2)]
                            + [child]
                            + outgoings[int(len(outgoings) / 2) :]
                        )
                        break
            grid.distribute_children(node, outgoings)

    grid.resolve_collisions()
    grid.collapse_grid()

    return grid


def calc_layout_data(
    flow_class,
    edge_start_gap_size=EDGE_START_GAP_SIZE,
    edge_end_gap_size=EDGE_END_GAP_SIZE,
):
    # Topological nodes sort, and edge cycle breaking
    nodes, _ = topsort(flow_class)

    # Topologically sorted incoming edges
    incoming_edges = {
        node: sorted(
            [edge.src for edge in node._incoming()], key=lambda node: nodes.index(node)
        )
        for node in nodes
    }

    # Topologically sorted outgoing edges
    outgoing_edges = {
        node: sorted(
            [edge.dst for edge in node._outgoing()], key=lambda node: nodes.index(node)
        )
        for node in nodes
    }

    # Place nodes on a grid
    grid = layout(nodes, incoming_edges, outgoing_edges)

    init_shapes(grid)

    # boundary events sit on their host's border; the synthetic host ->
    # boundary and host -> compensation-handler edges exist only for grid
    # placement and are not drawn
    snap_boundary_events(grid)
    grid.edges = [
        edge
        for edge in grid.edges
        if edge.edge_class not in ("boundary", "compensation")
    ]

    calc_edges(
        grid,
        edge_start_gap_size=edge_start_gap_size,
        edge_end_gap_size=edge_end_gap_size,
    )
    calc_text(grid)

    grid.flow_class = flow_class

    return grid


def snap_boundary_events(grid):
    """Overlap each boundary event shape onto its host task's bottom border."""
    attached_count = {}
    for cell in grid.cells:
        host_node = getattr(cell.node, "_attached_to", None)
        if host_node is None:
            continue
        host = grid[host_node]
        position = attached_count.get(host_node, 0)
        attached_count[host_node] = position + 1

        cell.shape.x = (
            host.shape.x + host.shape.width - (position + 1) * (cell.shape.width + 5)
        )
        cell.shape.y = host.shape.y + host.shape.height - cell.shape.height // 2


def init_shapes(grid):
    # init shapes
    for cell in grid.cells:
        shape = getattr(cell.node, "shape", DEFAULT_SHAPE)
        cell.shape.width = shape["width"]
        cell.shape.height = shape["height"]
        cell.shape.svg = shape["svg"]
        if getattr(cell.node, "_multi_instance", False):
            # parallel multi-instance marker at the bottom center
            cell.shape.svg += (
                '<path d="M {x} {y} v 9 m 5 -9 v 9 m 5 -9 v 9"'
                ' fill="none" stroke="rgb(0, 0, 0)" stroke-width="2"/>'.format(
                    x=cell.shape.width // 2 - 5, y=cell.shape.height - 12
                )
            )

    # calc rows and col sizes; boundary event shapes are snapped onto their
    # host later, so they don't claim room in their own grid slot, while
    # host rows get extra headroom for the protruding event circles
    cells = list(grid.cells)
    if not cells:
        # a flow with no renderable nodes -- render an empty diagram rather
        # than crashing on max() of an empty grid
        grid.width = grid.height = 0
        return grid
    row_sizes = [0] * max(cell.row + 1 for cell in cells)
    col_sizes = [0] * max(cell.col + 1 for cell in cells)
    for cell in grid.cells:
        if getattr(cell.node, "_attached_to", None) is not None:
            continue
        height = cell.shape.height
        if getattr(cell.node, "_boundary_events", None):
            height += 35
        row_sizes[cell.row] = max(row_sizes[cell.row], height)
        col_sizes[cell.col] = max(col_sizes[cell.col], cell.shape.width)

    # set shapes positions
    for cell in grid.cells:
        cell.x = sum(col_sizes[: cell.col]) + GAP_SIZE * cell.col
        cell.y = sum(row_sizes[: cell.row]) + GAP_SIZE * cell.row

        cell.width = col_sizes[cell.col]
        if cell.shape.width < col_sizes[cell.col]:
            cell.shape.x = cell.x + int((col_sizes[cell.col] - cell.shape.width) / 2)
        else:
            # is it ever happens?
            cell.shape.x = cell.x

        # avoid svg top cut
        if cell.shape.x == 0:
            cell.shape.x = 1

        cell.height = row_sizes[cell.row]
        if cell.shape.height < row_sizes[cell.row]:
            cell.shape.y = cell.y + int((row_sizes[cell.row] - cell.shape.height) / 2)
        else:
            cell.shape.y = cell.y

        # avoid svg left cut
        if cell.shape.y == 0:
            cell.shape.y = 1

    grid.width = sum(col_sizes) + GAP_SIZE * len(col_sizes)
    grid.height = sum(row_sizes) + GAP_SIZE * len(row_sizes)
    return grid


class Channels(object):
    """Distribute parallel edge runs over lanes inside grid gaps."""

    def __init__(self, step=GAP_SIZE // 4, lanes=3):
        self.step = step
        self.lanes = lanes
        self.used = {}

    def offset(self, kind, index):
        lane = self.used.get((kind, index), 0)
        self.used[(kind, index)] = lane + 1
        return self.step * (1 + lane % self.lanes)


def shape_rects(grid):
    return [
        (cell.node, (cell.shape.x, cell.shape.y, cell.shape.width, cell.shape.height))
        for cell in grid.cells
    ]


def segment_blocked(rects, p1, p2, exclude):
    """Check an axis-aligned segment against foreign node shapes."""
    (x1, y1), (x2, y2) = p1, p2
    for node, (rx, ry, rw, rh) in rects:
        if node in exclude:
            continue
        if x1 == x2 and rx + 1 < x1 < rx + rw - 1:
            lo, hi = min(y1, y2), max(y1, y2)
            if lo < ry + rh - 1 and hi > ry + 1:
                return True
        elif y1 == y2 and ry + 1 < y1 < ry + rh - 1:
            lo, hi = min(x1, x2), max(x1, x2)
            if lo < rx + rw - 1 and hi > rx + 1:
                return True
    return False


def path_blocked(rects, segments, exclude):
    return any(
        segment_blocked(rects, p1, p2, exclude)
        for p1, p2 in zip(segments, segments[1:])
    )


def channel_route(channels, src_cell, dst_cell, edge_start_gap_size, edge_end_gap_size):
    """Route an edge through the empty gaps between grid rows and columns."""
    src_cx = src_cell.shape.x + int(src_cell.shape.width / 2)
    dst_cy = dst_cell.shape.y + int(dst_cell.shape.height / 2)
    channel_y = src_cell.y + src_cell.height + channels.offset("h", src_cell.row)
    if dst_cell.col >= src_cell.col and dst_cell.col > 0:
        channel_x = dst_cell.x - GAP_SIZE + channels.offset("v", dst_cell.col - 1)
        entry = [dst_cell.shape.x - edge_end_gap_size, dst_cy]
    else:
        channel_x = dst_cell.x + dst_cell.width + channels.offset("v", dst_cell.col)
        entry = [dst_cell.shape.x + dst_cell.shape.width + edge_end_gap_size, dst_cy]
    return [
        [src_cx, src_cell.shape.y + src_cell.shape.height + edge_start_gap_size],
        [src_cx, channel_y],
        [channel_x, channel_y],
        [channel_x, dst_cy],
        entry,
    ]


def calc_edges(
    grid, edge_start_gap_size=EDGE_START_GAP_SIZE, edge_end_gap_size=EDGE_END_GAP_SIZE
):
    channels = Channels()
    rects = shape_rects(grid)

    for edge in grid.edges:
        src_cell = grid[edge.src]
        dst_cell = grid[edge.dst]

        segments = direct_route(
            edge,
            src_cell,
            dst_cell,
            channels,
            edge_start_gap_size,
            edge_end_gap_size,
            grid,
        )
        if path_blocked(rects, segments, {edge.src, edge.dst}):
            segments = channel_route(
                channels, src_cell, dst_cell, edge_start_gap_size, edge_end_gap_size
            )
        edge.segments = segments

        if edge.label and len(edge.segments) > 1:
            (x1, y1), (x2, y2) = edge.segments[0], edge.segments[1]
            if y1 == y2:  # horizontal start
                edge.label_pos = (min(x1, x2) + 10, y1 - 6)
            elif y2 > y1:  # heading down
                edge.label_pos = (x1 + 8, y1 + 16)
            else:  # heading up
                edge.label_pos = (x1 + 8, y1 - 10)


def direct_route(
    edge,
    src_cell,
    dst_cell,
    channels,
    edge_start_gap_size,
    edge_end_gap_size,
    grid=None,
):
    # Boundary event edges leave the circle from its bottom, drop into the
    # channel below the host row, then run to the target -- the BPMN
    # convention of a boundary flow dangling off the bottom of the task.
    host_node = getattr(edge.src, "_attached_to", None)
    if host_node is not None and grid is not None and host_node in grid.grid:
        host_cell = grid[host_node]
        cx = src_cell.shape.x + int(src_cell.shape.width / 2)
        circle_bottom = src_cell.shape.y + src_cell.shape.height
        # dangle into the channel below the host row, never above the circle
        channel_y = max(
            host_cell.y + host_cell.height, circle_bottom
        ) + channels.offset("h", host_cell.row)
        dst_cx = dst_cell.shape.x + int(dst_cell.shape.width / 2)
        if channel_y <= dst_cell.shape.y:
            entry_y = dst_cell.shape.y - edge_end_gap_size
        else:
            entry_y = dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size
        return [
            [cx, circle_bottom],
            [cx, channel_y],
            [dst_cx, channel_y],
            [dst_cx, entry_y],
        ]

    # Boundary event shapes are snapped away from their grid slot, so the
    # direction is classified by the drawn shape geometry, not by row/col.
    dx = (dst_cell.shape.x + int(dst_cell.shape.width / 2)) - (
        src_cell.shape.x + int(src_cell.shape.width / 2)
    )
    dy = (dst_cell.shape.y + int(dst_cell.shape.height / 2)) - (
        src_cell.shape.y + int(src_cell.shape.height / 2)
    )
    if abs(dx) <= 2:
        dx = 0
    if abs(dy) <= 2:
        dy = 0

    if dy == 0 and dx > 0:  # →
        return [
            [
                src_cell.shape.x + src_cell.shape.width + edge_start_gap_size,
                src_cell.shape.y + int(src_cell.shape.height / 2),
            ],
            [
                dst_cell.shape.x - edge_end_gap_size,
                dst_cell.shape.y + int(dst_cell.shape.height / 2),
            ],
        ]
    elif dy > 0 and dx > 0:  # ↘
        if len(list(edge.src._outgoing())) > 1:
            return [
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.shape.y + src_cell.shape.height + edge_start_gap_size,
                ],
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    dst_cell.shape.y + int(dst_cell.shape.height / 2),
                ],
                [
                    dst_cell.shape.x - edge_end_gap_size,
                    dst_cell.shape.y + int(dst_cell.shape.height / 2),
                ],
            ]
        else:
            return [
                [
                    src_cell.shape.x + src_cell.shape.width + edge_start_gap_size,
                    src_cell.shape.y + int(src_cell.shape.height / 2),
                ],
                [
                    dst_cell.shape.x + int(dst_cell.shape.width / 2),
                    src_cell.shape.y + int(src_cell.shape.height / 2),
                ],
                [
                    dst_cell.shape.x + int(dst_cell.shape.width / 2),
                    dst_cell.shape.y - edge_end_gap_size,
                ],
            ]
    elif dy > 0 and dx == 0:  # ↓
        return [
            [
                src_cell.shape.x + int(src_cell.shape.width / 2),
                src_cell.shape.y + src_cell.shape.height + edge_start_gap_size,
            ],
            [
                dst_cell.shape.x + int(dst_cell.shape.width / 2),
                dst_cell.shape.y - edge_end_gap_size,
            ],
        ]
    elif dy > 0 and dx < 0:  # ↙
        channel_y = src_cell.y + src_cell.height + channels.offset("h", src_cell.row)
        return [
            [
                src_cell.shape.x + int(src_cell.shape.width / 2),
                src_cell.shape.y + src_cell.shape.height + edge_start_gap_size,
            ],
            [src_cell.shape.x + int(src_cell.shape.width / 2), channel_y],
            [dst_cell.shape.x + int(3 * dst_cell.shape.width / 4), channel_y],
            [
                dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                dst_cell.shape.y - edge_end_gap_size,
            ],
        ]
    elif dy == 0 and dx < 0:  # ←
        # a back-edge loops below the row and returns up into the dst's
        # bottom border; the channel must clear the dst endpoint so the
        # final approach points up (into the host), not down
        dst_entry_y = dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size
        channel_y = max(src_cell.y + src_cell.height, dst_entry_y) + channels.offset(
            "h", src_cell.row
        )
        return [
            [
                src_cell.shape.x + int(src_cell.shape.width / 2),
                src_cell.shape.y + src_cell.shape.height + edge_start_gap_size,
            ],
            [src_cell.shape.x + int(src_cell.shape.width / 2), channel_y],
            [dst_cell.shape.x + int(3 * dst_cell.shape.width / 4), channel_y],
            [dst_cell.shape.x + int(3 * dst_cell.shape.width / 4), dst_entry_y],
        ]
    elif dy < 0 and dx < 0:  # ↖
        channel_y = src_cell.y - channels.offset("h", src_cell.row - 1)
        return [
            [
                src_cell.shape.x + int(src_cell.shape.width / 2),
                src_cell.shape.y - edge_start_gap_size,
            ],
            [src_cell.shape.x + int(src_cell.shape.width / 2), channel_y],
            [dst_cell.shape.x + int(3 * dst_cell.shape.width / 4), channel_y],
            [
                dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size,
            ],
        ]
    elif dy < 0 and dx == 0:  # ↑
        return [
            [
                src_cell.shape.x + int(src_cell.shape.width / 2),
                src_cell.shape.y - edge_start_gap_size,
            ],
            [
                dst_cell.shape.x + int(dst_cell.shape.width / 2),
                dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size,
            ],
        ]
    elif dy < 0 and dx > 0:  # ↗
        if len(list(edge.src._outgoing())) > 1:
            return [
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.shape.y - edge_start_gap_size,
                ],
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    dst_cell.shape.y + int(dst_cell.shape.height / 2),
                ],
                [
                    dst_cell.shape.x - edge_end_gap_size,
                    dst_cell.shape.y + int(dst_cell.shape.height / 2),
                ],
            ]
        else:
            return [
                [
                    src_cell.shape.x + src_cell.shape.width + edge_start_gap_size,
                    src_cell.shape.y + int(src_cell.shape.height / 2),
                ],
                [
                    dst_cell.shape.x + int(dst_cell.shape.width / 2),
                    src_cell.shape.y + int(src_cell.shape.height / 2),
                ],
                [
                    dst_cell.shape.x + int(dst_cell.shape.width / 2),
                    dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size,
                ],
            ]
    return []


def calc_text(grid):
    for cell in grid.cells:
        shape = getattr(cell.node, "shape", DEFAULT_SHAPE)
        text_align = shape.get("text-align")
        font_size = shape.get("font-size", 12)

        if cell.node.task_title:
            title = force_str(cell.node.task_title)
        else:
            title = " ".join(cell.node.name.capitalize().split("_"))

        if text_align == "middle":
            segments = wrap(title, 20)
            block_height = max(len(segments) - 1, 0) * font_size * 1.2

            x_start = int(cell.shape.width / 2)
            y_start = int((cell.shape.height - block_height) / 2)

            for n, segment in enumerate(segments):
                cell.shape.text.append(
                    (
                        segment,
                        "align-middle",
                        font_size,
                        x_start,
                        y_start + (n * font_size * 1.2),
                    )
                )
        else:
            cell.title = title


def calc_cell_status(flow_class, grid, process_pk):
    tasks = flow_class.task_class._default_manager.filter(
        process_id=process_pk, process__flow_class=flow_class
    ).order_by("flow_task", "created")
    tasks_group = dict(
        (k, list(v)) for k, v in groupby(tasks, lambda task: task.flow_task)
    )
    for flow_task in grid.nodes:
        for task in tasks_group.get(flow_task, []):
            if grid[flow_task].status is not None and task.status == STATUS.NEW:
                pass  # don't touch new tasks
            else:
                grid[flow_task].status = task.status


def grid_to_svg(grid):
    svg_template = get_template("viewflow/workflow/graph.svg")
    return svg_template.render({"grid": grid, "cells": grid.cells, "edges": grid.edges})


def grid_to_bpmn(grid):
    bpmn_template = get_template("viewflow/workflow/graph.bpmn")

    # Nodes without a BPMN counterpart (e.g. Obsolete) are dropped together
    # with their edges, so every sourceRef/targetRef resolves within the file.
    cells = [cell for cell in grid.cells if getattr(cell.node, "bpmn_element", None)]
    visible = {cell.node for cell in cells}
    edges = [edge for edge in grid.edges if edge.src in visible and edge.dst in visible]

    process_id, process_name = "id_process", ""
    if grid.flow_class is not None:
        try:
            label = grid.flow_class.instance.flow_label
        except AttributeError:
            # flow class outside any installed app (e.g. defined in a shell)
            label = grid.flow_class.__name__.lower()
        process_id = "id_process_" + re.sub(r"[^A-Za-z0-9_.-]", "_", label)
        process_name = force_str(grid.flow_class.process_title or "")

    # synthesize a compensation boundary event + association per host with
    # a registered .CompensateWith handler
    compensations = []
    for cell in cells:
        handler = getattr(cell.node, "_compensation_handler", None)
        if handler is None or handler not in grid.grid:
            continue
        handler_cell = grid[handler]
        # match the size of real boundary events (see nodes/boundary.py)
        size = 36
        x = cell.shape.x + 5
        y = cell.shape.y + cell.shape.height - size // 2
        compensations.append(
            {
                "id": f"id_node_{cell.node.name}_compensation",
                "host_name": cell.node.name,
                "handler_name": handler.name,
                "x": x,
                "y": y,
                "size": size,
                "waypoints": [
                    (x + size // 2, y + size),
                    (
                        handler_cell.shape.x + int(handler_cell.shape.width / 2),
                        handler_cell.shape.y,
                    ),
                ],
            }
        )

    return bpmn_template.render(
        {
            "grid": grid,
            "cells": cells,
            "edges": edges,
            "process_id": process_id,
            "process_name": process_name,
            "compensations": compensations,
        }
    )

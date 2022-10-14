# coding: utf-8
from __future__ import division

import math
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
    'width': 150,
    'height': 100,
    'svg': """
        <rect class="task" width="150" height="100" rx="5" ry="5"/>
    """
}


class Edge(object):
    __slots__ = ['src', 'dst', 'segments']

    def __init__(self, src, dst, segments=None):
        self.src = src
        self.dst = dst
        self.segments = segments if segments is not None else []


class Shape(object):
    __slots__ = ['x', 'y', 'width', 'height', 'svg', 'text']

    def __init__(self, x=-1, y=-1, width=-1, height=-1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = []

    def label(self):
        return ' '.join(segment[0] for segment in self.text)


class Cell(object):
    __slots__ = ['col', 'row', 'x', 'y', 'width', 'height', 'node', 'shape', 'status']

    def __init__(self, node, col=-1, row=-1, x=-1, y=-1, width=-1, height=-1, shape=None, status=None):
        self.node = node
        self.col = col
        self.row = row
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape if shape is not None else Shape()
        self.status = status

    def incoming(self):
        return self.node._incoming()

    def outgoing(self):
        return self.node._outgoing()


class Grid(object):
    def __init__(self, nodes):
        self.width = -1
        self.height = -1

        self.grid = {
            node: Cell(node)
            for node in nodes
        }
        self.edges = [
            Edge(edge.src, edge.dst)
            for node in nodes
            for edge in node._incoming()]

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
        above = children[0: int(math.floor(half))]
        middle = children[int(math.floor(half)):int(math.ceil(half))]
        below = children[int(math.ceil(half)):]
        for child in above:
            self.insert_row_above(parent_cell.row)
            self[child].row = parent_cell.row - 1
        for child in middle:
            self[child].row = parent_cell.row
        for child in reversed(below):
            self.insert_row_below(parent_cell.row)
            self[child].row = parent_cell.row + 1

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
        """Optimize grid by removing empty cells in between."""
        # TODO


def topsort(flow_class):
    result, incoming_to_reverse = [], {}

    nodes = list(flow_class.instance.nodes())
    incoming_edges = {
        node: {edge.src for edge in node._incoming()}
        for node in nodes
    }
    initial_incoming = {
        node: set(incoming_edges[node])
        for node in nodes
    }

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
        key=lambda split: incoming_splits[0].index(split)
    )

    if not common_splits:
        return None

    return common_splits[0]


def layout(nodes, incoming_edges, outgoing_edges):
    grid = Grid(nodes)

    for node in nodes:
        incomings, outgoings = incoming_edges[node], outgoing_edges[node]
        placed_incomings = [incoming for incoming in incomings if grid[incoming].col != -1]

        if len(placed_incomings) == 0:
            grid.place_start_node(node)
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
                        outgoings = outgoings[0:int(len(outgoings) / 2)] + [child] + outgoings[int(len(outgoings) / 2):]
                        break
            grid.distribute_children(node, outgoings)

    grid.collapse_grid()

    return grid


def calc_layout_data(flow_class, edge_start_gap_size=EDGE_START_GAP_SIZE, edge_end_gap_size=EDGE_END_GAP_SIZE):
    # Topological nodes sort, and edge cycle breaking
    nodes, _ = topsort(flow_class)

    # Topologically sorted incoming edges
    incoming_edges = {
        node: sorted(
            [edge.src for edge in node._incoming()],
            key=lambda node: nodes.index(node))
        for node in nodes
    }

    # Topologically sorted outgoing edges
    outgoing_edges = {
        node: sorted(
            [edge.dst for edge in node._outgoing()],
            key=lambda node: nodes.index(node))
        for node in nodes
    }

    # Place nodes on a grid
    grid = layout(nodes, incoming_edges, outgoing_edges)

    # hack fix
    for cell1 in grid.cells:
        for cell2 in grid.cells:
            if cell1.node != cell2.node and cell1.row == cell2.row and cell1.col == cell2.col:
                cell1.row += 1

    init_shapes(grid)
    calc_edges(grid, edge_start_gap_size=edge_start_gap_size, edge_end_gap_size=edge_end_gap_size)
    calc_text(grid)

    return grid


def init_shapes(grid):
    # init shapes
    for cell in grid.cells:
        shape = getattr(cell.node, 'shape', DEFAULT_SHAPE)
        cell.shape.width = shape['width']
        cell.shape.height = shape['height']
        cell.shape.svg = shape['svg']

    # calc rows and col sizes
    row_sizes = [0] * max(cell.row + 1 for cell in grid.cells)
    col_sizes = [0] * max(cell.col + 1 for cell in grid.cells)
    for cell in grid.cells:
        row_sizes[cell.row] = max(row_sizes[cell.row], cell.shape.height)
        col_sizes[cell.col] = max(col_sizes[cell.col], cell.shape.width)

    # set shapes positions
    for cell in grid.cells:
        cell.x = sum(col_sizes[:cell.col]) + GAP_SIZE * cell.col
        cell.y = sum(row_sizes[:cell.row]) + GAP_SIZE * cell.row

        cell.width = col_sizes[cell.col]
        if cell.shape.width < col_sizes[cell.col]:
            cell.shape.x = cell.x + int((col_sizes[cell.col] - cell.shape.width) / 2)
        else:
            # is it ever happens?
            cell.shape.x = cell.x

        cell.height = row_sizes[cell.row]
        if cell.shape.height < row_sizes[cell.row]:
            cell.shape.y = cell.y + int((row_sizes[cell.row] - cell.shape.height) / 2)
        else:
            cell.shape.y = cell.y

    grid.width = sum(col_sizes) + GAP_SIZE * len(col_sizes)
    grid.height = sum(row_sizes) + GAP_SIZE * len(row_sizes)
    return grid


def calc_edges(grid, edge_start_gap_size=EDGE_START_GAP_SIZE, edge_end_gap_size=EDGE_END_GAP_SIZE):
    for edge in grid.edges:
        src_cell = grid[edge.src]
        dst_cell = grid[edge.dst]

        if src_cell.row == dst_cell.row and src_cell.col < dst_cell.col:  # →
            edge.segments = [
                [
                    src_cell.shape.x + src_cell.shape.width + edge_start_gap_size,
                    src_cell.shape.y + int(src_cell.shape.height / 2)
                ],
                [
                    dst_cell.shape.x - edge_end_gap_size,
                    dst_cell.shape.y + int(dst_cell.shape.height / 2)
                ]
            ]
        elif src_cell.row < dst_cell.row and src_cell.col < dst_cell.col:  # ↘
            if len(list(edge.src._outgoing())) > 1:
                edge.segments = [
                    [
                        src_cell.shape.x + int(src_cell.shape.width / 2),
                        src_cell.shape.y + src_cell.shape.height + edge_start_gap_size
                    ],
                    [
                        src_cell.shape.x + int(src_cell.shape.width / 2),
                        dst_cell.shape.y + int(dst_cell.shape.height / 2),
                    ],
                    [
                        dst_cell.shape.x - edge_end_gap_size,
                        dst_cell.shape.y + int(dst_cell.shape.height / 2),
                    ]
                ]
            else:
                edge.segments = [
                    [
                        src_cell.shape.x + src_cell.shape.width + edge_start_gap_size,
                        src_cell.shape.y + int(src_cell.shape.height / 2)
                    ],
                    [
                        dst_cell.shape.x + int(dst_cell.shape.width / 2),
                        src_cell.shape.y + int(src_cell.shape.height / 2)
                    ],
                    [
                        dst_cell.shape.x + int(dst_cell.shape.width / 2),
                        dst_cell.shape.y - edge_end_gap_size
                    ]
                ]
        elif src_cell.row < dst_cell.row and src_cell.col == dst_cell.col:  # ↓
            edge.segments = [
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.shape.y + src_cell.shape.height + edge_start_gap_size
                ],
                [
                    dst_cell.shape.x + int(dst_cell.shape.width / 2),
                    dst_cell.shape.y - edge_end_gap_size
                ]
            ]
        elif src_cell.row < dst_cell.row and src_cell.col > dst_cell.col:  # ↙
            edge.segments = [
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.shape.y + src_cell.shape.height + edge_start_gap_size
                ],
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.y + src_cell.height + GAP_SIZE // 2
                ],
                [
                    dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                    src_cell.y + src_cell.height + GAP_SIZE // 2
                ],
                [
                    dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                    dst_cell.shape.y - edge_end_gap_size
                ]
            ]
        elif src_cell.row == dst_cell.row and src_cell.col > dst_cell.col:  # ←
            edge.segments = [
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.shape.y + src_cell.shape.height + edge_start_gap_size
                ],
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.y + src_cell.height + int(4 * GAP_SIZE // 5)
                ],
                [
                    dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                    src_cell.y + src_cell.height + int(4 * GAP_SIZE // 5)
                ],
                [
                    dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                    dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size
                ]
            ]
        elif src_cell.row > dst_cell.row and src_cell.col > dst_cell.col:  # ↖
            edge.segments = [
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.shape.y - edge_start_gap_size
                ],
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.y - GAP_SIZE // 2
                ],
                [
                    dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                    src_cell.y - GAP_SIZE // 2
                ],
                [
                    dst_cell.shape.x + int(3 * dst_cell.shape.width / 4),
                    dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size
                ]
            ]
        elif src_cell.row > dst_cell.row and src_cell.col == dst_cell.col:  # ↑
            edge.segments = [
                [
                    src_cell.shape.x + int(src_cell.shape.width / 2),
                    src_cell.shape.y - edge_start_gap_size
                ],
                [
                    dst_cell.shape.x + int(dst_cell.shape.width / 2),
                    dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size
                ]
            ]
        elif src_cell.row > dst_cell.row and src_cell.col < dst_cell.col:  # ↗
            if len(list(edge.src._outgoing())) > 1:
                edge.segments = [
                    [
                        src_cell.shape.x + int(src_cell.shape.width / 2),
                        src_cell.shape.y - edge_start_gap_size
                    ],
                    [
                        src_cell.shape.x + int(src_cell.shape.width / 2),
                        dst_cell.shape.y + int(dst_cell.shape.height / 2)
                    ],
                    [
                        dst_cell.shape.x - edge_end_gap_size,
                        dst_cell.shape.y + int(dst_cell.shape.height / 2)
                    ]
                ]
            else:
                edge.segments = [
                    [
                        src_cell.shape.x + src_cell.shape.width + edge_start_gap_size,
                        src_cell.shape.y + int(src_cell.shape.height / 2)
                    ],
                    [
                        dst_cell.shape.x + int(dst_cell.shape.width / 2),
                        src_cell.shape.y + int(src_cell.shape.height / 2)
                    ],
                    [
                        dst_cell.shape.x + int(dst_cell.shape.width / 2),
                        dst_cell.shape.y + dst_cell.shape.height + edge_end_gap_size
                    ]
                ]


def calc_text(grid):
    for cell in grid.cells:
        shape = getattr(cell.node, 'shape', DEFAULT_SHAPE)
        text_align = shape.get('text-align')
        font_size = shape.get('font-size', 12)
        if text_align == 'middle':
            if cell.node.task_title:
                title = force_str(cell.node.task_title)
            else:
                title = ' '.join(cell.node.name.capitalize().split('_'))
            segments = wrap(title, 20)
            block_height = max(len(segments) - 1, 0) * font_size * 1.2

            x_start = int(cell.shape.width / 2)
            y_start = int((cell.shape.height - block_height) / 2)

            for n, segment in enumerate(segments):
                cell.shape.text.append(
                    (
                        segment, 'align-middle', font_size,
                        x_start,
                        y_start + (n * font_size * 1.2)
                    )
                )


def calc_cell_status(flow_class, grid, process_pk):
    tasks = flow_class.task_class._default_manager.filter(
        process_id=process_pk,
        process__flow_class=flow_class
    ).order_by(
        'flow_task', 'created'
    )
    tasks_group = dict(
        (k, list(v))
        for k, v in groupby(tasks, lambda task: task.flow_task)
    )
    for flow_task in grid.nodes:
        for task in tasks_group.get(flow_task, []):
            if grid[flow_task].status is not None and task.status == STATUS.NEW:
                pass  # don't touch new tasks
            else:
                grid[flow_task].status = task.status


def grid_to_svg(grid):
    svg_template = get_template('viewflow/workflow/graph.svg')
    return svg_template.render({
        'grid': grid,
        'cells': grid.cells,
        'edges': grid.edges})


def grid_to_bpmn(grid):
    svg_template = get_template('viewflow/workflow/graph.bpmn')
    return svg_template.render({
        'grid': grid,
        'cells': grid.cells,
        'edges': grid.edges})

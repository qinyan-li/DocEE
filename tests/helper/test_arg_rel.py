import pytest
import torch

from dee.helper.arg_rel import AdjMat, SpanRelAdjMat
from dee.modules import adj_decoding
from dee.utils import extract_combinations_from_event_objs, remove_combination_roles
from dee.event_types import get_event_template


@pytest.fixture
def tmp_event_type_fields_list_for_test():
    template = get_event_template("zheng2019_trigger_graph")
    return template.event_type_fields_list


def test_span_rel_adj_from_eval_instance(tmp_event_type_fields_list_for_test):
    adj = SpanRelAdjMat(
        [
            ((3, 0), (7, 1), (5, 2), (9, 3), (10, 4), (11, 5), (4, 6), (8, 7)),
            ((3, 0), (5, 2), (9, 3), (11, 5), (4, 6), (12, 7), (6, 8)),
        ],
        13,
    )
    a = adj[2, 3]
    adj = AdjMat(
        [
            ((3, 0), (7, 1), (5, 2), (9, 3), (10, 4), (11, 5), (4, 6), (8, 7)),
            ((3, 0), (5, 2), (9, 3), (11, 5), (4, 6), (12, 7), (6, 8)),
        ],
        13,
        tmp_event_type_fields_list_for_test,
    )
    b = adj[2, 3]
    assert a == b


def test_span_rel_adj(tmp_event_type_fields_list_for_test):
    adj = SpanRelAdjMat([(1,)], 1)
    with pytest.raises(AssertionError):
        adj.array_index2linear_index(0, 0)
    assert adj.linear_index2array_index(0) == (0, 0)

    adj = SpanRelAdjMat([(0, 1)], 2)
    with pytest.raises(AssertionError):
        adj.array_index2linear_index(0, 0)
    assert adj.array_index2linear_index(0, 1) == 0
    with pytest.raises(AssertionError):
        adj.array_index2linear_index(1, 1)

    adj = SpanRelAdjMat([(1, 2, 3, 4, 5, 6)], 9)
    assert adj.array_index2linear_index(0, 1) == 0
    assert adj.array_index2linear_index(0, 8) == 7
    assert adj.array_index2linear_index(7, 8) == 35
    assert adj.array_index2linear_index(0, 5) == 4
    assert adj.array_index2linear_index(5, 8) == 32
    assert adj.array_index2linear_index(3, 4) == 21
    assert adj.array_index2linear_index(1, 4) == 10
    assert adj.array_index2linear_index(4, 7) == 28
    assert adj.array_index2linear_index(3, 6) == 23

    assert adj.linear_index2array_index(0) == (0, 1)
    assert adj.linear_index2array_index(7) == (0, 8)
    assert adj.linear_index2array_index(35) == (7, 8)
    assert adj.linear_index2array_index(4) == (0, 5)
    assert adj.linear_index2array_index(32) == (5, 8)
    assert adj.linear_index2array_index(21) == (3, 4)
    assert adj.linear_index2array_index(10) == (1, 4)
    assert adj.linear_index2array_index(28) == (4, 7)
    assert adj.linear_index2array_index(23) == (3, 6)

    adj = SpanRelAdjMat([(0, 1, 2, 3), (0, 4, 5, 6), (2, 5, 6, 7)], 8)
    assert adj.reveal_adj_mat() == [
        [-1, 1, 1, 1, 1, 1, 1, 0],
        [1, -1, 1, 1, 0, 0, 0, 0],
        [1, 1, -1, 1, 0, 1, 1, 1],
        [1, 1, 1, -1, 0, 0, 0, 0],
        [1, 0, 0, 0, -1, 1, 1, 0],
        [1, 0, 1, 0, 1, -1, 1, 1],
        [1, 0, 1, 0, 1, 1, -1, 1],
        [0, 0, 1, 0, 0, 1, 1, -1],
    ]
    adj = AdjMat(
        [(0, 1, 2, 3), (0, 4, 5, 6), (2, 5, 6, 7)],
        8,
        tmp_event_type_fields_list_for_test,
    )
    assert adj.tolist(-1) == [
        [-1, 1, 1, 1, 1, 1, 1, 0],
        [1, -1, 1, 1, 0, 0, 0, 0],
        [1, 1, -1, 1, 0, 1, 1, 1],
        [1, 1, 1, -1, 0, 0, 0, 0],
        [1, 0, 0, 0, -1, 1, 1, 0],
        [1, 0, 1, 0, 1, -1, 1, 1],
        [1, 0, 1, 0, 1, 1, -1, 1],
        [0, 0, 1, 0, 0, 1, 1, -1],
    ]


def test_combination_case1(tmp_event_type_fields_list_for_test):
    gold_combinations = [(3, 4, 5, 6, 7, 8, 9, 10, 11, 12)]
    adj = SpanRelAdjMat(gold_combinations, 13)
    revealed_mat = adj.reveal_adj_mat()
    assert revealed_mat == [
        [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, -1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, -1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, -1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, -1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, -1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, -1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, -1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, -1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
    ]

    adj = AdjMat(gold_combinations, 13, tmp_event_type_fields_list_for_test)
    assert adj.tolist(-1) == [
        [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, -1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, -1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, -1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, -1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, -1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, -1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, -1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, -1, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1],
    ]

    pred_combinations = adj_decoding.bron_kerbosch_pivoting_decode(revealed_mat, 3)
    assert len(set(gold_combinations) & set(pred_combinations)) >= 1

    tensor_mat = torch.tensor(revealed_mat)
    tensor_mat = torch.bitwise_or(tensor_mat, tensor_mat.T)
    assert revealed_mat == tensor_mat.tolist()


def test_combination_case2(tmp_event_type_fields_list_for_test):
    event_obj_list = [
        None,
        None,
        None,
        None,
        [
            ((3, 0), (14, 1), (6, 2), (15, 3), (16, 4), (18, 5), (8, 6), (9, 7)),
            ((3, 0), (11, 1), (7, 2), (15, 3), (16, 4), (18, 5), (4, 6), (12, 7)),
            ((3, 0), (5, 1), (6, 2), (15, 3), (16, 4), (18, 5), (4, 6), (9, 7)),
            ((3, 0), (6, 2), (15, 3), (16, 4), (18, 5), (9, 7)),
        ],
    ]
    gold_combinations = extract_combinations_from_event_objs(event_obj_list)
    gold_combinations = remove_combination_roles(gold_combinations)
    assert gold_combinations == {
        (3, 6, 8, 9, 14, 15, 16, 18),
        (3, 4, 5, 6, 9, 15, 16, 18),
        (3, 6, 9, 15, 16, 18),
        (3, 4, 7, 11, 12, 15, 16, 18),
    }

    adj_rel = SpanRelAdjMat(event_obj_list, 19, whole_graph=True)
    adj_mat = adj_rel.reveal_adj_mat()
    assert adj_mat == [
        [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, -1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 1, -1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, -1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, -1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0, 0, -1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 0, 0, 1, 0, -1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, 1, 0, 1, -1, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, -1, 1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, -1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, -1, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, -1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, -1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, -1],
    ]

    adj_rel = AdjMat(
        event_obj_list, 19, tmp_event_type_fields_list_for_test, whole_graph=True
    )
    adj_mat = adj_rel.reveal_adj_mat(-1, tolist=True)
    assert adj_mat == [
        [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, -1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 1, -1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, -1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, -1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0, 0, -1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 0, 0, 1, 0, -1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, 1, 0, 1, -1, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, -1, 1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, -1, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, -1, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, -1, 1, 0, 1],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, -1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, -1],
    ]
    smooth_mat = adj_rel.smooth_tensor_rel_mat()
    assert smooth_mat.cpu().tolist() == [
        [
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        [
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.5,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.05000000074505806,
            0.5,
            0.05000000074505806,
            0.05000000074505806,
            0.05000000074505806,
            0.0,
            0.05000000074505806,
            0.0,
            0.05000000074505806,
            0.05000000074505806,
            0.0,
            0.0,
            0.05000000074505806,
            0.05000000074505806,
            0.0,
            0.05000000074505806,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.5,
            0.0714285746216774,
            0.0,
            0.0,
            0.0714285746216774,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0714285746216774,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0555555559694767,
            0.0555555559694767,
            0.0555555559694767,
            0.5,
            0.0,
            0.0555555559694767,
            0.0555555559694767,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0555555559694767,
            0.0555555559694767,
            0.0555555559694767,
            0.0,
            0.0555555559694767,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0,
            0.5,
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0714285746216774,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0,
            0.0,
            0.0714285746216774,
            0.0,
            0.5,
            0.0714285746216774,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0714285746216774,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0555555559694767,
            0.0555555559694767,
            0.0555555559694767,
            0.0555555559694767,
            0.0,
            0.0555555559694767,
            0.5,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0555555559694767,
            0.0555555559694767,
            0.0555555559694767,
            0.0,
            0.0555555559694767,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0,
            0.0714285746216774,
            0.0,
            0.0,
            0.0,
            0.5,
            0.0714285746216774,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0714285746216774,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0,
            0.0714285746216774,
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.5,
            0.0,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0714285746216774,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0714285746216774,
            0.0,
            0.0,
            0.0714285746216774,
            0.0,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0,
            0.0,
            0.0,
            0.5,
            0.0714285746216774,
            0.0714285746216774,
            0.0,
            0.0714285746216774,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.5,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.5,
            0.0,
            0.0416666679084301,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
        ],
        [
            0.0,
            0.0,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.0416666679084301,
            0.0416666679084301,
            0.0416666679084301,
            0.0,
            0.5,
        ],
    ]
    # plot_graph_from_adj_mat(adj_mat, title="test_case2")

    # pred_combinations = set(adj_decoding.bron_kerbosch_decode(adj_mat, 3))
    # pred_combinations = set(adj_decoding.bron_kerbosch_pivoting_decode(adj_mat, 3))
    # pred_combinations = set(adj_decoding.brute_force_adj_decode(adj_mat, 3))
    # for gc in gold_combinations:
    #     if gc not in pred_combinations:
    #         print(gc)
    # print(pred_combinations)
    # print(gold_combinations)
    # assert gold_combinations, pred_combinations)


def test_directed_graph(tmp_event_type_fields_list_for_test):
    event_obj_list = [
        [[None, 5, 6, 2, 3, None, 4, None]],
        None,
        [[1, 0, None, 3, 2, None]],
        None,
        None,
    ]
    adj = AdjMat(
        event_obj_list,
        7,
        tmp_event_type_fields_list_for_test,
        whole_graph=True,
        trigger_aware_graph=True,
        num_triggers=3,
    )
    assert adj.tolist(-1) == [
        [-1, 1, 1, 1, 0, 0, 0],
        [1, -1, 1, 1, 0, 0, 0],
        [1, 1, -1, 0, 0, 1, 1],
        [1, 1, 0, -1, 0, 1, 1],
        [0, 0, 0, 0, -1, 1, 1],
        [0, 0, 1, 1, 1, -1, 1],
        [0, 0, 1, 1, 1, 1, -1],
    ]

    adj = AdjMat(
        event_obj_list,
        7,
        tmp_event_type_fields_list_for_test,
        whole_graph=True,
        trigger_aware_graph=True,
        directed_graph=True,
        num_triggers=3,
    )
    assert adj.tolist(-1) == [
        [-1, 1, 1, 1, 0, 0, 0],
        [1, -1, 1, 1, 0, 0, 0],
        [0, 0, -1, 0, 0, 0, 0],
        [0, 0, 0, -1, 0, 0, 0],
        [0, 0, 0, 0, -1, 0, 0],
        [0, 0, 1, 1, 1, -1, 1],
        [0, 0, 1, 1, 1, 1, -1],
    ]

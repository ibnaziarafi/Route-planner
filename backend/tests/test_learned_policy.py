"""Real artifact inference and feasibility checks; no training during tests."""
from collections import Counter
import json
import numpy as np
import pytest
from backend.ml import policy
from backend.ml.instances import SPLITS, instance


def test_split_sets_are_disjoint():
    assert set(SPLITS['train']).isdisjoint(SPLITS['validation'])
    assert set(SPLITS['train']).isdisjoint(SPLITS['test'])
    assert set(SPLITS['validation']).isdisjoint(SPLITS['test'])


def test_artifact_is_actually_trained_and_finite():
    metadata = policy.model_metadata()
    assert metadata['available'] is True
    assert metadata['total_episodes'] == 1000
    for mode in ['save', 'time']:
        vector = policy.load_weights(mode)
        assert vector.shape == (14,)
        assert np.all(np.isfinite(vector))
        assert np.linalg.norm(vector) > .01
        assert metadata['selection'][mode]['episode'] > 0


@pytest.mark.parametrize('mode', ['save','time'])
@pytest.mark.parametrize('seed', [2000,2001,2002])
def test_frozen_inference_deterministic_and_shipments_feasible(mode, seed):
    drivers, orders, dm, economics, timing, _ = instance(seed)
    kwargs = dict(mode=mode, economics=economics, timing=timing)
    first = policy.solve(orders, drivers, dm, **kwargs)
    second = policy.solve(orders, drivers, dm, **kwargs)
    assert first.as_dict() == second.as_dict()
    assert first.unassigned_orders == []
    expected = Counter((o.order_id, kind) for o in orders for kind in ('pickup', 'dropoff'))
    actual = Counter((s.order_id, s.stop_type.value) for r in first.routes.values() for s in r.stops)
    assert actual == expected
    by_order = {o.order_id:o for o in orders}
    for driver in drivers:
        route = first.routes[driver.driver_id]
        if mode == 'time':
            assert route.stops
        load = 0
        picked = set()
        node = driver.start_node
        for stop in route.stops:
            assert np.isfinite(dm.cost(node, stop.node))
            if stop.stop_type.value == 'pickup':
                picked.add(stop.order_id)
                load += by_order[stop.order_id].demand
            else:
                assert stop.order_id in picked
                load -= by_order[stop.order_id].demand
            assert 0 <= load <= driver.capacity
            node = stop.node
        assert load == 0


def test_missing_artifact_never_falls_back(monkeypatch, tmp_path):
    monkeypatch.setattr(policy, 'ARTIFACT_PATH', tmp_path/'absent.json')
    assert not policy.model_metadata()['available']
    with pytest.raises(RuntimeError, match='unavailable'):
        policy.load_weights('save')


def test_malformed_artifact_rejected(monkeypatch, tmp_path):
    p = tmp_path/'bad.json'
    p.write_text(json.dumps({'feature_version':policy.FEATURE_VERSION, 'weights':{'save':[float('nan')]*14,'time':[0]*14}}))
    monkeypatch.setattr(policy, 'ARTIFACT_PATH', p)
    with pytest.raises(ValueError):
        policy.load_weights('save')

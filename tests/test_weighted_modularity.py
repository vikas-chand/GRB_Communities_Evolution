"""The weighted modularity of the collapsed graph must equal the modularity of
the literal multigraph for any membership. igraph's VertexClustering.modularity
and leidenalg's .modularity property both silently ignore weights, which is the
bug this test pins down (found by external audit, 2026-08-22)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def test_weighted_equals_multigraph():
    import leidenalg as la
    from consensus import build, collapse, wq
    g = build()
    h = collapse(g)
    p = la.find_partition(h, la.RBConfigurationVertexPartition,
                          weights=h.es["weight"], resolution_parameter=1.0,
                          n_iterations=2, seed=1)
    m = list(p.membership)
    assert abs(wq(h, m, h.es["weight"]) - g.modularity(m)) < 1e-12

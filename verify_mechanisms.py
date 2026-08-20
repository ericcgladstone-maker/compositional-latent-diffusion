#!/usr/bin/env python3
"""Functional verification: drive every parameter/mechanism and assert it does
what its description claims. Reports PASS/FAIL per check. Run before trusting a
build. This is the directed, per-mechanism check that caught the reversibility
bug (manifest nodes never lapsed because _count_required shortcut them to full).
"""

from abm import config as C
from abm import phases as P
from abm.model import World, Agent

CHECKS = []
def check(name):
    def deco(fn):
        CHECKS.append((name, fn)); return fn
    return deco

def W(**over):
    return World(C.validate_config(over))

def fresh(world, idx=0, held=()):
    a = world.agents[idx]
    a.held = set(held); a.order = list(held); a.chunks=set(); a.latent=set()
    a.manifest=set(); a.variant={}
    return a


# ---------------- structure ----------------
@check("n_big_things creates that many big things")
def _():
    assert len(W(n_big_things=3).big_things) == 3

@check("requirement_size sets the defining-set size")
def _():
    w=W(requirement_size=5); assert len(w.big_things[0].required)==5

@check("sufficiency_k: k held -> latent, k-1 -> not")
def _():
    w=W(sufficiency_k=3, element_overlap=0)
    bt=w.big_things[0]; req=list(bt.required)
    a=fresh(w, held=req[:3]); assert w._is_latent_for(a,bt) is True
    a=fresh(w, held=req[:2]); assert w._is_latent_for(a,bt) is False

@check("element_overlap: shared elements belong to both big things")
def _():
    w=W(element_overlap=2)
    owners=w.element_owners
    shared=[e for e,o in owners.items() if len(o)>1]
    assert len(shared)==2, f"expected 2 shared, got {len(shared)}"

@check("requirement_encoding: additive needs full set, set_sufficiency needs k")
def _():
    req=list(W().big_things[0].required)
    ws=W(requirement_encoding="set_sufficiency", sufficiency_k=3, element_overlap=0)
    wa=W(requirement_encoding="additive", requirement_size=4, sufficiency_k=3, element_overlap=0)
    bt_s=ws.big_things[0]; bt_a=wa.big_things[0]
    a=fresh(ws, held=req[:3]); b=fresh(wa, held=req[:3])
    assert ws._is_latent_for(a,bt_s) is True   # 3 of 4 enough
    assert wa._is_latent_for(b,bt_a) is False   # additive needs all 4

# ---------------- transmissibility ----------------
@check("elements_only: big things never transfer whole")
def _():
    w=W(transmissibility_mode="elements_only")
    s=fresh(w,0); s.manifest={0}; r=fresh(w,1)
    assert w._whole_package_candidates(s,r)==[]

@check("whole_package: receiver adopts on one contact")
def _():
    w=W(transmissibility_mode="whole_package")
    s=fresh(w,0); s.manifest={0}; r=fresh(w,1)
    w._contact(s,r,1.0); assert 0 in r.manifest

@check("both: whole transfer only to an equipped receiver")
def _():
    w=W(transmissibility_mode="both", sufficiency_k=3)
    s=fresh(w,0); s.manifest={0}
    bt=w.big_things[0]
    unready=fresh(w,1)                              # holds nothing
    ready=fresh(w,2, held=list(bt.required)[:2])    # holds k-1, equipped
    assert w._whole_package_candidates(s,unready)==[]
    assert 0 in w._whole_package_candidates(s,ready)

# ---------------- network ----------------
@check("topology: each builds; uniform_mixing is complete")
def _():
    import abm.topology as T
    n=W().n
    full=W(topology="uniform_mixing").edges()
    assert len(full)==n*(n-1)//2, "uniform_mixing should be complete graph"
    for topo in ("small_world","ring_lattice","random"):
        assert len(W(topology=topo).edges())>0

@check("mean_degree: higher degree -> more edges")
def _():
    lo=len(W(topology="small_world", mean_degree=4).edges())
    hi=len(W(topology="small_world", mean_degree=12).edges())
    assert hi>lo, f"{hi} !> {lo}"

# ---------------- capacity & eviction ----------------
@check("capacity never exceeded over a run")
def _():
    w=W(seed=3, run_length=400); w.run()
    assert all(w._capacity_used(a)<=w.cfg["capacity"] for a in w.agents)

@check("eviction recency drops the oldest-held element")
def _():
    w=W(capacity=6, eviction_rule="recency", element_overlap=0)
    a=fresh(w, held=[0,1,2,3,4,5])           # order = [0..5], oldest=0
    w._add_element(a, 6)                      # forces eviction
    assert 0 not in a.held and len(a.held)==6

@check("eviction value_weighted protects near-complete sets")
def _():
    w=W(capacity=4, eviction_rule="value_weighted", element_overlap=1)
    a=fresh(w, held=[0,1,2,7])               # at cap; 0,1,2 feed alpha (val 3), 7 = noise (val 0)
    w._add_element(a, 4)                      # adding 5th forces an eviction
    assert 7 not in a.held and {0,1,2} <= a.held   # noise evicted, alpha pieces kept

@check("incompatibility on: a node holds at most one big thing; off: can hold both")
def _():
    won=W(incompatibility=True, seed=3); won.run()
    assert max(len(a.manifest) for a in won.agents) <= 1
    woff=W(incompatibility=False, seed=3); woff.run()
    assert any(len(a.manifest)==2 for a in woff.agents)

@check("reversible_adoption on: lapse below threshold; off: persist")
def _():
    won=W(reversible_adoption=True, element_overlap=1)
    a=fresh(won, held=[0,1,2]); a.manifest={0}; a.variant={0:(0,1,2)}
    a.held.discard(2); won._recompute_latent(a)
    assert 0 not in a.manifest, "should have lapsed"
    woff=W(reversible_adoption=False); b=fresh(woff, held=[0,1]); b.manifest={0}
    woff._recompute_latent(b); assert 0 in b.manifest, "should persist"

# ---------------- transmission dynamics ----------------
@check("transmission_prob=0 -> no spread; >0 -> spread")
def _():
    w0=W(transmission_prob=0.0, loss_rate=0.0, seed=1, run_length=80);
    s0=w0.history[0]["element_saturation"]; w0.run()
    assert abs(w0.history[-1]["element_saturation"]-s0)<1e-9, "no spread expected"
    w1=W(transmission_prob=0.3, seed=1, run_length=80); s1=w1.history[0]["element_saturation"]; w1.run()
    assert w1.history[-1]["element_saturation"]>s1

@check("loss_rate>0 erodes holdings (no inflow)")
def _():
    w=W(transmission_prob=0.0, loss_rate=0.4, seed=1, initial_element_density=0.5, run_length=40)
    start=sum(len(a.held) for a in w.agents); w.run()
    assert sum(len(a.held) for a in w.agents)<start

@check("contacts_per_tick: more contacts -> faster spread")
def _():
    a=W(contacts_per_tick=1, seed=2, run_length=40); a.run()
    b=W(contacts_per_tick=5, seed=2, run_length=40); b.run()
    assert b.history[-1]["element_saturation"]>=a.history[-1]["element_saturation"]

@check("scheduling: both run and stay valid")
def _():
    for s in ("asynchronous","synchronous"):
        w=W(scheduling=s, seed=1, run_length=50); w.run()
        assert all(w._capacity_used(x)<=w.cfg["capacity"] for x in w.agents)

@check("run_length caps history; quiescence can stop early")
def _():
    w=W(run_length=120, quiescence_window=0, seed=1); w.run()
    assert len(w.history)<=121
    wq=W(transmission_prob=0.0, loss_rate=0.0, quiescence_window=20, run_length=500, seed=1); wq.run()
    assert wq.history[-1]["t"]<500, "should quiesce early with no movement"

# ---------------- mechanisms ----------------
@check("compression: activation collapses elements into a chunk")
def _():
    w=W(compression=True, seed=4, run_length=600); w.run()
    assert any(len(a.chunks)>=1 for a in w.agents)

@check("differential_slot_cost: a chunk costs 2 slots")
def _():
    w=W(compression=True, differential_slot_cost=True)
    a=fresh(w); a.chunks={0}
    assert w._capacity_used(a)==2
    w2=W(compression=True, differential_slot_cost=False); a2=fresh(w2); a2.chunks={0}
    assert w2._capacity_used(a2)==1

@check("stabilization + boost=0 makes adopted elements immovable under loss")
def _():
    w=W(stabilization=True, stabilization_boost=0.0, loss_rate=1.0, element_overlap=0)
    bt=w.big_things[0]; a=fresh(w, held=list(bt.required)); a.manifest={0}
    w._do_loss()
    assert a.held & bt.required_set, "stabilized elements should survive loss"

@check("stabilization off: loss removes elements")
def _():
    w=W(stabilization=False, loss_rate=1.0, element_overlap=0)
    bt=w.big_things[0]; a=fresh(w, held=list(bt.required)); a.manifest={0}
    w._do_loss(); assert not a.held

@check("enhanced_transmission raises send prob for an adopter's elements")
def _():
    w=W(enhanced_transmission=True, enhanced_factor=3.0, transmission_prob=0.1)
    s=fresh(w); s.manifest={0}; e=w.big_things[0].required[0]
    base=W(enhanced_transmission=False, transmission_prob=0.1)
    sb=fresh(base); sb.manifest={0}
    assert w._send_prob(s,e,1.0) > base._send_prob(sb,e,1.0)

@check("tie_strength_channels assigns weak and strong ties")
def _():
    w=W(tie_strength_channels=True, strong_tie_fraction=0.3, seed=1)
    vals={round(s,2) for row in w.tie_strength for s in row}
    assert vals<= {0.1,1.0} and 1.0 in vals

@check("strong_tie_fraction: higher fraction -> more strong ties")
def _():
    def frac_strong(f):
        w=W(tie_strength_channels=True, strong_tie_fraction=f, seed=1)
        tot=sum(len(r) for r in w.tie_strength); strong=sum(1 for r in w.tie_strength for s in r if s>0.5)
        return strong/tot
    assert frac_strong(0.4) > frac_strong(0.05)

@check("coupling_strength=0 -> accept factor neutral (off)")
def _():
    w=W(internal_coupling=True, coupling_strength=0.0)
    r=fresh(w); r.manifest={0}
    assert abs(w._accept_factor(r, w.big_things[1].required[0]) - 1.0) < 1e-9

@check("internal_coupling negative: holding one big thing suppresses another's element")
def _():
    w=W(internal_coupling=True, coupling_strength=-0.5, coupling_level="big_thing", n_big_things=2)
    r=fresh(w); r.manifest={0}                       # holds alpha
    e_beta=[e for e in w.big_things[1].required if e not in w.big_things[0].required_set][0]
    assert w._accept_factor(r, e_beta) < 1.0

@check("neighbor_coupling: neighbors' big thing shifts your acceptance")
def _():
    w=W(neighbor_coupling=True, coupling_strength=-0.6, seed=1, n_big_things=2)
    r=w.agents[0]; fresh(w,0)
    for j in w.adjacency[0]: fresh(w,j); w.agents[j].manifest={0}   # neighbors hold alpha
    e_beta=[e for e in w.big_things[1].required if e not in w.big_things[0].required_set][0]
    assert w._accept_factor(r, e_beta) < 1.0

# ---------------- seeding ----------------
@check("initial_element_density: higher -> more initial holdings")
def _():
    lo=sum(len(a.held) for a in W(initial_element_density=0.1, seed=1).agents)
    hi=sum(len(a.held) for a in W(initial_element_density=0.4, seed=1).agents)
    assert hi>lo

@check("seeding single_source concentrates elements in few agents")
def _():
    w=W(seeding_scheme="single_source", seed=1)
    holders=sum(1 for a in w.agents if a.held)
    assert holders <= 0.2*w.n, f"{holders} holders, expected few"

@check("change_agent_scenario injects equipped, manifest minority")
def _():
    w=W(change_agent_scenario=True, change_agent_fraction=0.1, seed=1)
    cas=[a for a in w.agents if a.is_change_agent]
    assert len(cas)>=1 and all(a.manifest for a in cas)

@check("change_agent_fraction scales the minority size")
def _():
    n=W().n
    small=sum(1 for a in W(change_agent_scenario=True, change_agent_fraction=0.05, seed=1).agents if a.is_change_agent)
    big=sum(1 for a in W(change_agent_scenario=True, change_agent_fraction=0.2, seed=1).agents if a.is_change_agent)
    assert big>small

@check("change_agent_evangelism multiplies their send prob")
def _():
    w=W(change_agent_scenario=True, change_agent_evangelism=4.0, seed=1, transmission_prob=0.1)
    ca=next(a for a in w.agents if a.is_change_agent)
    e=next(iter(ca.held))
    base=W(change_agent_scenario=True, change_agent_evangelism=1.0, seed=1, transmission_prob=0.1)
    cb=next(a for a in base.agents if a.is_change_agent); eb=next(iter(cb.held))
    assert w._send_prob(ca,e,1.0) > base._send_prob(cb,eb,1.0)

# ---------------- trigger ----------------
@check("exogenous trigger fires only at multiples of trigger_time")
def _():
    w=W(trigger_type="exogenous", trigger_time=50, seed=1, run_length=160); w.run()
    assert all(t%50==0 for t in w.trigger_fired_at)

@check("trigger_reach<1 leaves some latent unflipped at a firing")
def _():
    # many ready agents, partial reach -> not all flip in one trigger
    w=W(trigger_type="exogenous", trigger_time=1, trigger_reach=0.3,
        initial_element_density=0.5, seed=2, run_length=1)
    w.step()
    still_latent=sum(1 for a in w.agents if a.latent)
    assert still_latent>0, "partial reach should leave some latent"

@check("endogenous trigger fires from neighbor conditions, not a clock")
def _():
    w=W(trigger_type="endogenous", endogenous_trigger_threshold=0.1,
        initial_element_density=0.4, seed=1, run_length=200); w.run()
    assert w.history[-1]["manifest_share"]>0   # something manifested without a global clock

# ---------------- reproducibility ----------------
@check("seed: identical seed -> identical outcome")
def _():
    cfg=dict(seed=7, run_length=200)
    assert W(**cfg).run()[-1]["manifest_share"]==W(**cfg).run()[-1]["manifest_share"]


def main():
    width=58
    passed=failed=0
    for name, fn in CHECKS:
        try:
            fn(); print(f"  PASS  {name}"); passed+=1
        except AssertionError as e:
            print(f"  FAIL  {name}\n          -> {e}"); failed+=1
        except Exception as e:
            print(f"  ERROR {name}\n          -> {type(e).__name__}: {e}"); failed+=1
    print(f"\n{passed} passed, {failed} failed, {len(CHECKS)} total")

if __name__ == "__main__":
    main()

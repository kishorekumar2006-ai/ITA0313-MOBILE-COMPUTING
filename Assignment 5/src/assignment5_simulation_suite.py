#!/usr/bin/env python3
"""Assignment 5 CO5 reproducible simulation suite.

All outputs are synthetic model results, not measurements from a physical Android device.
Run from the package root:
    python src/assignment5_simulation_suite.py
"""
from __future__ import annotations
import csv, itertools, json, math, random
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/"results"; FIG=ROOT/"figures"
RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
random.seed(505)
plt.rcParams.update({"font.size":10,"text.color":"black","axes.labelcolor":"black",
                     "xtick.color":"black","ytick.color":"black","axes.edgecolor":"black",
                     "figure.facecolor":"white","axes.facecolor":"white"})

def write_csv(name, headers, rows):
    with (RES/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)

def save(fig,name):
    fig.tight_layout(); fig.savefig(FIG/name,dpi=180,bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- B1: constraint-aware background work ----------
TASKS=[
 {"id":"R01","priority":5,"size_kb":18,"sensitive":False,"encrypted":True,"kind":"sensor","min_battery":10,"network":"ANY"},
 {"id":"R02","priority":9,"size_kb":12,"sensitive":True,"encrypted":True,"kind":"critical","min_battery":5,"network":"ANY"},
 {"id":"R03","priority":3,"size_kb":740,"sensitive":True,"encrypted":True,"kind":"sync","min_battery":25,"network":"UNMETERED"},
 {"id":"R04","priority":7,"size_kb":42,"sensitive":True,"encrypted":True,"kind":"alert","min_battery":5,"network":"ANY"},
 {"id":"R05","priority":2,"size_kb":310,"sensitive":False,"encrypted":True,"kind":"analytics","min_battery":35,"network":"UNMETERED"},
 {"id":"R06","priority":8,"size_kb":85,"sensitive":True,"encrypted":True,"kind":"sync","min_battery":15,"network":"CONNECTED"},
 {"id":"R07","priority":4,"size_kb":22,"sensitive":False,"encrypted":True,"kind":"sensor","min_battery":10,"network":"ANY"},
 {"id":"R08","priority":6,"size_kb":160,"sensitive":True,"encrypted":True,"kind":"sync","min_battery":20,"network":"CONNECTED"},
]
def constraints(task, env):
    if not env["permission"]: return "CANCEL_PERMISSION"
    if task["sensitive"] and not task["encrypted"]: return "REJECT_UNENCRYPTED"
    if env["logout"]: return "CANCEL_LOGOUT"
    if env["battery"] < task["min_battery"]: return "DEFER_LOW_BATTERY"
    if env["doze"] and task["kind"] not in ("critical","alert"): return "DEFER_DOZE"
    if task["network"]=="UNMETERED" and env["network"]!="WIFI": return "DEFER_NETWORK"
    if task["network"]=="CONNECTED" and env["network"]=="OFFLINE": return "DEFER_NETWORK"
    return "EXECUTE"

def run_scheduler(tasks, env, strategy):
    pending=[dict(t) for t in tasks]
    if strategy=="priority":
        pending.sort(key=lambda t:(-t["priority"], t["size_kb"], t["id"]))
    events=[]; success=[]; deferred=[]; cancelled=[]; workers=[]
    for t in pending:
        decision=constraints(t,env)
        if decision=="EXECUTE":
            success.append(t["id"]); workers.append(1)
            outcome="SUCCESS"
        elif decision.startswith("DEFER"):
            deferred.append(t["id"]); outcome=decision
        else:
            cancelled.append(t["id"]); outcome=decision
        events.append([strategy,t["id"],t["priority"],env["battery"],env["network"],int(env["doze"]),int(env["permission"]),decision,outcome])
    return {"enqueued":len(tasks),"successful":success,"deferred":deferred,"cancelled":cancelled,
            "peak_workers":min(2,len(success)),"events":events,"backlog":deferred}

def simulate_b1():
    envs={
      "good":{"battery":82,"network":"WIFI","doze":False,"permission":True,"logout":False},
      "doze_low":{"battery":12,"network":"METERED","doze":True,"permission":True,"logout":False},
      "permission_revoked":{"battery":75,"network":"WIFI","doze":False,"permission":False,"logout":False},
    }
    rows=[]; sched=[]
    for scenario,env in envs.items():
        for strat in ("fifo","priority"):
            r=run_scheduler(TASKS,env,strat)
            sched.append((scenario,strat,r))
            rows.extend([[scenario]+e[1:] for e in r["events"]])
    write_csv("b1_background_decisions.csv",
      ["scenario","task_id","priority","battery_percent","network","doze","permission","decision","outcome"],rows)
    summary=[]
    for sc,st,r in sched:
        summary.append([sc,st,r["enqueued"],len(r["deferred"]),len(r["cancelled"]),len(r["successful"]),r["peak_workers"],";".join(r["backlog"])])
    write_csv("b1_scheduler_summary.csv",["scenario","strategy","enqueued","deferred","cancelled","successful","peak_concurrent_workers","backlog_ids"],summary)
    # Compare order of successful critical tasks in good conditions
    good=[x for x in sched if x[0]=="good"]
    fig,ax=plt.subplots(figsize=(7,4))
    names=["FIFO","Priority"]
    critical=[]
    for _,st,r in good:
        critical.append(sum(1 for x in r["successful"] if next(t for t in TASKS if t["id"]==x)["priority"]>=8))
    ax.bar(names,critical,color="white",edgecolor="black",hatch=["///","xxx"])
    ax.set_ylabel("Critical/high-priority items completed"); ax.set_title("B1 – Scheduler comparison (same good-network workload)")
    ax.grid(axis="y",linestyle=":",color="gray"); save(fig,"b1_scheduler_comparison.png")
    return summary

# ---------- B2: adversarial workload structure ----------
def b2_simulate():
    easy=[{"id":f"E{i:02d}","priority":8 if i%3==0 else 4,"battery":65,"network":"WIFI","encrypted":True,"retry":0} for i in range(10)]
    hard=[{"id":f"H{i:02d}","priority":9 if i%3==0 else 3,"battery":12 if i%2==0 else 22,"network":"OFFLINE" if i%3==0 else "METERED","encrypted":i%4!=0,"retry":0} for i in range(10)]
    rows=[]; summary=[]
    for label,items in [("A_easy",easy),("B_adversarial",hard)]:
        successes=deferred=reject=processed=retries=0
        for it in items:
            processed+=1
            if not it["encrypted"]:
                decision="REJECT_SECURITY"; reject+=1
            elif it["battery"]<20 or it["network"]=="OFFLINE":
                decision="DEFER"; deferred+=1; it["retry"]+=1; retries+=1
            elif it["network"]=="METERED" and it["priority"]<8:
                decision="DEFER_METERED"; deferred+=1; it["retry"]+=1; retries+=1
            else:
                decision="DELIVERED"; successes+=1
            rows.append([label,it["id"],it["priority"],it["battery"],it["network"],it["encrypted"],decision,it["retry"]])
        summary.append([label,len(items),processed,successes,deferred,reject,retries])
    write_csv("b2_workload_trace.csv",["workload","record_id","priority","battery_percent","network","encrypted","decision","retry_count"],rows)
    write_csv("b2_workload_summary.csv",["workload","input_records","processed","delivered","deferred","security_rejected","retry_events"],summary)
    fig,ax=plt.subplots(figsize=(7,4))
    labels=[r[0] for r in summary]; delivered=[r[3] for r in summary]; deferred=[r[4] for r in summary]; rejected=[r[5] for r in summary]
    x=range(2); ax.bar(x,delivered,label="Delivered",edgecolor="black",color="white")
    ax.bar(x,deferred,bottom=delivered,label="Deferred",edgecolor="black",hatch="///",color="white")
    ax.bar(x,rejected,bottom=[delivered[i]+deferred[i] for i in x],label="Rejected",edgecolor="black",hatch="xxx",color="white")
    ax.set_xticks(list(x),labels); ax.set_ylabel("Records"); ax.set_title("B2 – Same input size, different structural difficulty")
    ax.legend(); ax.grid(axis="y",linestyle=":",color="gray"); save(fig,"b2_workload_comparison.png")
    return summary

# ---------- B3: exact vs adaptive feed optimization ----------
QUALITIES=[("low",0.72,0.60,0.55),("medium",0.88,0.85,0.72),("high",1.00,1.20,0.95)]
CACHES=[2,4,6,8]
PREFETCH=[1,2,3,4]
def config_cost(config, items, device):
    q,cache,pref=config
    quality,energy_factor,decode_ms=q[1],q[2],q[3]
    # Synthetic objective: frame-overrun penalty + estimated energy + visual-quality penalty
    avg_decode=decode_ms*(1+items/30)
    frame=avg_decode + 1.2*pref + 0.75*cache
    frame_penalty=max(0,frame-16)*2.6
    energy=items*(0.18*energy_factor + 0.025*cache + 0.04*pref)
    memory=cache*18 + pref*9
    quality_penalty=(1-quality)*items*1.3
    total=frame_penalty+energy+quality_penalty+max(0,memory-device["memory_budget"])*0.8
    return {"cost":round(total,3),"frame_ms":round(frame,3),"energy_units":round(energy,3),"memory_mb":memory,"quality":quality}

def exact_search(items,device):
    best=None; evaluated=0
    for q,c,p in itertools.product(QUALITIES,CACHES,PREFETCH):
        r=config_cost((q,c,p),items,device); evaluated+=1
        if best is None or r["cost"]<best["cost"]:
            best={"quality":q[0],"cache":c,"prefetch":p,**r}
    return best,evaluated

def adaptive_search(items,device):
    # Local adaptive search: reduce quality under frame pressure, shrink cache/prefetch under energy pressure.
    q=QUALITIES[2]; cache=6; pref=3; ops=0; evictions=0; changes=0
    for _ in range(8):
        ops+=1; m=config_cost((q,cache,pref),items,device)
        changed=False
        if m["frame_ms"]>16 and q!=QUALITIES[0]:
            q=QUALITIES[1] if q==QUALITIES[2] else QUALITIES[0]; changes+=1; changed=True
        elif (m["energy_units"]>device["energy_budget"] or m["memory_mb"]>device["memory_budget"]) and cache>2:
            cache-=2; evictions+=1; changed=True
        elif m["energy_units"]>device["energy_budget"] and pref>1:
            pref-=1; changed=True
        if not changed: break
    m=config_cost((q,cache,pref),items,device)
    return {"quality":q[0],"cache":cache,"prefetch":pref,**m,"operations":ops,"quality_changes":changes,"cache_evictions":evictions}

def simulate_b3():
    cases=[
      ("T1_small_balanced",6,{"memory_budget":150,"energy_budget":12}),
      ("T2_medium",18,{"memory_budget":150,"energy_budget":22}),
      ("T3_low_memory",24,{"memory_budget":75,"energy_budget":25}),
      ("T4_counterexample",10,{"memory_budget":150,"energy_budget":60}),
    ]
    rows=[]
    for name,items,dev in cases:
        ex,n=exact_search(items,dev); ap=adaptive_search(items,dev)
        rows.append([name,items,ex["quality"],ex["cache"],ex["prefetch"],ex["cost"],n,ap["quality"],ap["cache"],ap["prefetch"],ap["cost"],ap["operations"],int(abs(ex["cost"]-ap["cost"])<1e-9)])
    write_csv("b3_small_instance_comparison.csv",["test_case","feed_items","exact_quality","exact_cache","exact_prefetch","exact_cost","exact_configurations_evaluated","adaptive_quality","adaptive_cache","adaptive_prefetch","adaptive_cost","adaptive_operations","costs_match"],rows)
    sizes=[8,16,32,64,128]
    scale=[]
    for nitems in sizes:
        # The candidate design space expands with feed size and resolution choices.
        quality_levels=3 + nitems//16
        cache_levels=3 + nitems//32
        prefetch_levels=2 + nitems//32
        exact_evaluated=0
        best_scaled=None
        for qi,ci,pi in itertools.product(range(quality_levels),range(cache_levels),range(prefetch_levels)):
            exact_evaluated += 1
            # A compact synthetic cost for the expanded configuration grid.
            qloss=(quality_levels-1-qi)*0.45*nitems
            ecost=0.12*nitems*(1+ci*0.15+pi*0.12)
            frame_penalty=max(0,(nitems/(qi+2))+ci*0.8+pi*0.6-16)*1.4
            total=qloss+ecost+frame_penalty
            if best_scaled is None or total<best_scaled:
                best_scaled=total
        ap=adaptive_search(nitems,{"memory_budget":180,"energy_budget":100})
        scale.append([nitems,quality_levels,cache_levels,prefetch_levels,exact_evaluated,ap["operations"],ap["quality_changes"],ap["cache_evictions"],round(best_scaled,3),ap["cost"]])
    write_csv("b3_scalability.csv",["feed_items","quality_levels","cache_levels","prefetch_levels","exact_configurations_evaluated","adaptive_iterations","adaptive_quality_changes","adaptive_cache_evictions","exact_scaled_cost","adaptive_cost"],scale)
    fig,ax=plt.subplots(figsize=(7,4))
    ax.plot([r[0] for r in scale],[r[4] for r in scale],marker="o",label="Exact configurations evaluated",color="black")
    ax.plot([r[0] for r in scale],[r[5] for r in scale],marker="s",label="Adaptive iterations",color="gray")
    ax.set_xlabel("Feed items"); ax.set_ylabel("Operation count"); ax.set_title("B3 – Exact versus adaptive operation counts")
    ax.legend(); ax.grid(True,linestyle=":",color="gray"); save(fig,"b3_operation_scalability.png")
    costs=[r[5] for r in rows]; ac=[r[10] for r in rows]
    fig,ax=plt.subplots(figsize=(7,4)); x=range(len(rows))
    ax.bar([i-.18 for i in x],costs,.36,label="Exact",edgecolor="black",color="white")
    ax.bar([i+.18 for i in x],ac,.36,label="Adaptive",edgecolor="black",hatch="///",color="white")
    ax.set_xticks(list(x),[r[0] for r in rows],rotation=12); ax.set_ylabel("Synthetic objective cost (lower is better)")
    ax.set_title("B3 – Exact and adaptive cost on small instances"); ax.legend(); ax.grid(axis="y",linestyle=":",color="gray"); save(fig,"b3_exact_vs_adaptive.png")
    return rows,scale

# ---------- B4: multimedia selection heuristic ----------
PROFILES=[
 {"device":"Entry-level","battery":18,"cpu":0.8,"network_mbps":2.0,"wifi":False},
 {"device":"Mid-range","battery":58,"cpu":1.4,"network_mbps":8.0,"wifi":True},
 {"device":"Flagship","battery":86,"cpu":2.2,"network_mbps":35.0,"wifi":True},
 {"device":"Adversarial radio-rich / low battery","battery":12,"cpu":1.8,"network_mbps":30.0,"wifi":True},
]
OPTIONS=[("480p",1.0,0.22,0.35),("720p",2.5,0.43,0.65),("1080p",5.0,0.82,1.20)]
def estimate_option(opt,profile):
    res,mbps,energy_per_min,quality=opt
    transfer_s=60*10*mbps/(profile["network_mbps"]*0.78)
    encode_s=60*10*(mbps/2.0)/profile["cpu"]
    total_s=transfer_s+encode_s
    energy=energy_per_min*10 + 0.003*total_s
    return {"resolution":res,"bitrate_mbps":mbps,"quality":quality,"time_s":round(total_s,1),"energy_units":round(energy,2)}
def heuristic(profile):
    # Conservative profile rule first chooses max candidate feasible under battery and network.
    candidates=[]
    for op in OPTIONS:
        m=estimate_option(op,profile)
        if op[1] <= profile["network_mbps"]*0.8 and m["energy_units"] <= max(1.0,profile["battery"]*0.35):
            candidates.append((op,m))
    if not candidates:
        op=OPTIONS[0]; m=estimate_option(op,profile); decision="DEFER_UNTIL_CHARGING_OR_BETTER_NETWORK"
    else:
        op,m=max(candidates,key=lambda x:x[0][3])
        decision="DEFER_LOW_BATTERY" if profile["battery"]<15 else ("UPLOAD_NOW" if profile["network_mbps"]>=4 else "QUEUE_FOR_WIFI")
    impact=100*m["energy_units"]/max(profile["battery"]*10,1)
    return {**m,"decision":decision,"battery_impact_percent":round(impact,2)}
def exact_multimedia(profile):
    best=None
    for op in OPTIONS:
        m=estimate_option(op,profile)
        # illustrative cost balances quality loss, completion delay, and energy
        score=(1-m["quality"])*20 + m["time_s"]*0.015 + m["energy_units"]*0.8
        if profile["battery"]<20: score += m["energy_units"]*2
        if best is None or score<best["score"]:
            best={**m,"score":score}
    return best
def simulate_b4():
    rows=[]
    for p in PROFILES:
        h=heuristic(p); e=exact_multimedia(p)
        rows.append([p["device"],p["battery"],p["cpu"],p["network_mbps"],h["resolution"],h["bitrate_mbps"],h["decision"],h["time_s"],h["energy_units"],h["battery_impact_percent"],e["resolution"],e["bitrate_mbps"],round(e["score"],3),int(h["resolution"]==e["resolution"])])
    write_csv("b4_multimedia_decisions.csv",["device_profile","battery_percent","cpu_factor","network_mbps","heuristic_resolution","heuristic_bitrate_mbps","upload_decision","estimated_completion_s","estimated_energy_units","estimated_battery_impact_percent","exhaustive_choice","exhaustive_bitrate_mbps","exhaustive_objective_score","same_resolution_as_exact"],rows)
    fig,ax=plt.subplots(figsize=(7,4)); labels=[r[0] for r in rows]
    y=[r[8] for r in rows]
    ax.bar(range(len(rows)),y,edgecolor="black",color="white",hatch="///")
    ax.set_xticks(range(len(rows)),labels,rotation=15); ax.set_ylabel("Estimated energy units (10-minute clip)")
    ax.set_title("B4 – Heuristic multimedia energy estimates"); ax.grid(axis="y",linestyle=":",color="gray"); save(fig,"b4_energy_estimates.png")
    return rows

def main():
    b1=simulate_b1(); b2=b2_simulate(); b3,scale=simulate_b3(); b4=simulate_b4()
    summary={"B1_scheduler_rows":len(b1),"B2_workloads":len(b2),"B3_cases":len(b3),"B3_scalability_points":len(scale),"B4_profiles":len(b4),
             "evidence_type":"SIMULATED deterministic educational models"}
    (RES/"execution_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("SIMULATION COMPLETE – synthetic educational outputs, not physical device measurements.")
    print(json.dumps(summary,indent=2))
    print(f"Generated CSV files: {len(list(RES.glob('*.csv')))}; figures: {len(list(FIG.glob('*.png')))}")
if __name__=="__main__": main()

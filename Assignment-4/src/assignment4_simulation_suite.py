"""Assignment 4 CO4 simulation suite.
All outputs are synthetic, deterministic educational model outputs, not device measurements.
Run from the package root: python simulations/assignment4_simulation_suite.py
"""
from __future__ import annotations
import csv, math, random
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures'
RES = ROOT / 'results'
FIG.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)
random.seed(404)

plt.rcParams.update({'font.size': 11, 'axes.edgecolor':'black', 'text.color':'black',
                     'axes.labelcolor':'black', 'xtick.color':'black', 'ytick.color':'black',
                     'figure.facecolor':'white', 'axes.facecolor':'white'})

def write_csv(name, headers, rows):
    with (RES/name).open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)

def savefig(fig, name):
    fig.tight_layout(); fig.savefig(FIG/name, dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig)

def simulate_os_states():
    rows=[
        ['Foreground','Resumed / active',0,180,'High','Remain alive unless extreme memory pressure'],
        ['Background for 5 min','Stopped / cached',500,176,'Lower','May remain cached; no guarantee of survival'],
        ['Low-memory event','Background cached process',900,118,'Very low','Trim caches; process may be killed by system'],
        ['Return after process death','New process / restored state',0,132,'High after launch','Recreate from persisted state; callbacks do not imply process survived'],
    ]
    write_csv('b1_os_process_state.csv',['condition','simulated_state','oom_adj_concept','resident_memory_mb','relative_importance','interpretation'],rows)
    x=['Foreground','Background 5 min','Low memory','Relaunch']
    mem=[180,176,118,132]
    fig,ax=plt.subplots(figsize=(8,4.5)); ax.plot(x,mem,marker='o',linewidth=2,color='black'); ax.set_ylabel('Illustrative resident memory (MB)'); ax.set_title('B1 – Simulated application process memory states'); ax.grid(True,linestyle=':',color='gray'); ax.tick_params(axis='x',rotation=12)
    savefig(fig,'b1_process_memory.png')
    # lifecycle event log: Android conceptual sequence only
    write_csv('b1_lifecycle_trace.csv',['case','time_s','event','state_or_effect'],[
        ['Foreground',0,'onCreate','Process created / activity initialised'],['Foreground',1,'onStart','Activity visible'],['Foreground',2,'onResume','Interaction enabled'],
        ['Background',0,'onPause','Loses foreground focus'],['Background',1,'onStop','No longer visible'],['Background',300,'cached','Process may remain cached; no callback guaranteed at kill'],
        ['Low memory',301,'trim memory signal','System asks app to release resources where callback applies'],['Low memory',302,'process reclaimed','Process death possible; not an Activity callback'],
        ['Relaunch',0,'new process','Persisted state read; Activity recreated; saved-state restoration conditional']])

def simulate_threading():
    # Base single-thread work: 50 ms per million abstract operations + fixed app setup.
    rows=[]
    for workload_m in [0.05,5,20,100]:
        work=50*workload_m
        single=12+work
        multi=12+(work*0.35)+1.5+4.0 # 4 workers: 0.25 ideal + 0.10 contention; setup/sync
        if workload_m<1: multi=12+work+4.0+1.5
        rows.append([workload_m,4,round(single,2),round(multi,2),round(single/multi,2),1,4,
                     round(34+workload_m*0.08,1),round(34+4*3+workload_m*0.10,1),
                     round(max(0, math.ceil(single/16.67)-1),1),round(max(0, math.ceil(11/16.67)-1),1),
                     'SIMULATED model; not profiler data'])
    write_csv('b2_threading_comparison.csv',['workload_million_ops','worker_threads','single_thread_ms','multi_thread_ms','speedup_ratio','single_thread_count','multi_thread_count','single_memory_mb','multi_memory_mb','single_frame_deadline_misses_per_task','multi_frame_deadline_misses_per_task','evidence_type'],rows)
    fig,ax=plt.subplots(figsize=(8,4.5)); sizes=[r[0] for r in rows]; ax.plot(sizes,[r[2] for r in rows],marker='o',label='Single thread'); ax.plot(sizes,[r[3] for r in rows],marker='s',label='4-thread executor'); ax.set_xlabel('Workload (million abstract operations)'); ax.set_ylabel('Simulated task duration (ms)'); ax.set_title('B2 – Large-workload threading comparison'); ax.legend(); ax.grid(True,linestyle=':',color='gray'); savefig(fig,'b2_threading_large.png')
    tiny=rows[0]
    fig,ax=plt.subplots(figsize=(7,4)); ax.bar(['Single thread','4-thread executor'],[tiny[2],tiny[3]],color=['white','lightgray'],edgecolor='black'); ax.set_ylabel('Simulated duration (ms)'); ax.set_title('B2 – Counter-example: small workload'); ax.grid(axis='y',linestyle=':',color='gray'); savefig(fig,'b2_threading_small.png')
    # scenario assumptions and core placement
    write_csv('b2_execution_trace.csv',['step','single_thread_design','parallel_design','reason'],[
        [1,'UI thread receives tap','UI thread enqueues task','Keep input handling responsive'],
        [2,'UI thread performs parse/filter','Executor splits chunks over 4 workers','Large tasks amortise scheduling'],
        [3,'UI blocked until complete','Workers join; result posted to UI','UI does not touch views off-thread'],
        [4,'Render delayed for long task','Render may proceed while workers run','Less jank when work is sufficiently large'],
        [5,'Small workload avoids pool setup','Small workload still pays dispatch/sync cost','Parallelism can be slower below crossover size']])

def simulate_runtime():
    # Modelled runtimes; time and heap figures are representative scenario values only.
    rows=[]
    dataset={
      'verify': [520,285,840,610,52,9,31,168],
      'speed-profile': [410,218,545,455,34,7,22,158],
      'speed': [465,230,495,420,30,6,19,181],
    }
    for mode,vals in dataset.items():
        rows.append([mode,*vals,'SIMULATED teaching model'])
    write_csv('b3_art_compilation_modes.csv',['compile_mode','cold_start_ms','warm_start_ms','cpu_bound_ms','allocation_workload_ms','list_render_ms','gc_events','total_gc_pause_ms','peak_heap_mb','evidence_type'],rows)
    fig,ax=plt.subplots(figsize=(8,4.5)); labels=list(dataset); x=range(3); width=.24
    for j,(metric,idx) in enumerate([('CPU-bound (ms)',3),('Allocation-heavy (ms)',4),('List render (ms)',5)]):
        ax.bar([i+(j-1)*width for i in x],[dataset[l][idx] for l in labels],width=width,label=metric,edgecolor='black',fill=[True,False,True][j],hatch=['','//','..'][j])
    ax.set_xticks(list(x),labels); ax.set_ylabel('Simulated execution time (ms)'); ax.set_title('B3 – ART compilation-mode model'); ax.legend(); ax.grid(axis='y',linestyle=':',color='gray'); savefig(fig,'b3_compile_modes.png')
    fig,ax=plt.subplots(figsize=(7.5,4.5)); steps=[0,1,2,3,4,5]; retained=[24,52,83,111,145,176]; ax.plot(steps,retained,marker='o',label='Retained heap with leak'); ax.axhline(128,color='black',linestyle='--',label='Illustrative pressure threshold'); ax.set_xlabel('Repeated benchmark iteration'); ax.set_ylabel('Retained heap (MB)'); ax.set_title('B3 – Simulated static-reference leak'); ax.legend(); ax.grid(True,linestyle=':',color='gray'); savefig(fig,'b3_memory_leak.png')
    write_csv('b3_leak_trace.csv',['iteration','retained_heap_mb','gc_count','gc_pause_ms','main_thread_stall_ms','interpretation'],[
        [0,24,0,0,8,'Baseline objects allocated and retained'],[1,52,1,4,11,'Static Activity reference prevents collection'],[2,83,2,8,16,'Heap growth continues after collection'],[3,111,3,11,31,'GC work increases; UI starts missing frame deadlines'],[4,145,4,18,120,'Severe stall; ANR risk rises'],[5,176,5,24,700,'Simulated watchdog threshold exceeded; ANR-like condition']])

def simulate_security():
    threats=[
      ['Spoofing','Forged session or API identity','Authentication token','Token replay / stolen credentials','Short-lived token, TLS, device-bound key','Low–medium'],
      ['Tampering','Modified local health record','Encrypted database record','Offline data integrity loss','AEAD encryption, MAC/hash, server version check','Low–medium'],
      ['Repudiation','User denies record submission','Audit event stream','No non-repudiable event trail','Server-side append-only audit and request ID','Medium'],
      ['Information disclosure','Local DB or token extracted','Local database / token','Patient-data exposure','App sandbox, encrypted DB, Keystore-backed key','Medium on rooted/unlocked device'],
      ['Denial of service','Flood sync endpoint / job queue','API service and local queue','Delayed emergency sync','Rate limit, bounded queue, retry backoff','Medium'],
      ['Elevation of privilege','Exported activity abused','Exported component','Unauthorized data access','Non-exported internal components, authz checks','Low'],
      ['Network interception','HTTP cleartext / invalid certificate','API traffic','Read/modify data in transit','TLS 1.2+ / modern TLS, hostname verification','Low if trust store correct'],
    ]
    write_csv('b4_stride_threats.csv',['stride_category','threat','asset','attack_vector','protection','residual_risk'],threats)
    assets=[
      ['Auth token','File read by another app','App sandbox + Keystore protected encryption','Blocked','Different UID cannot normally read private app files'],
      ['Local DB','Lost device / offline extraction','Encrypted DB + hardware-backed key + screen lock','Partially Blocked','Rooted/unlocked device or authenticated app can access plaintext'],
      ['API traffic','Wi-Fi interception','TLS with certificate and hostname validation','Blocked','Compromised endpoint/CA or app bypass remains possible'],
      ['Exported activity','External app invokes internal screen','Non-exported component + auth check','Blocked','Incorrectly exported deep link may reopen risk'],
      ['Camera data','Unauthorized camera access','Runtime permission + scoped capture','Partially Blocked','User-approved capture can still be misused by app logic'],
      ['Location data','Covert/background location access','Permission scope, foreground indication, minimisation','Partially Blocked','Granted access and OS/location precision depend on settings'],
    ]
    write_csv('b4_security_asset_audit.csv',['asset','attack_vector','mechanism_applied','result','reason'],assets)
    write_csv('b4_weakened_control.csv',['case','prediction','simulated_audit_result','why'],[
      ['Baseline TLS enabled','API traffic should be protected from passive interception','BLOCKED','TLS encrypts and authenticates channel in model'],
      ['Changed: cleartext HTTP allowed','Payload becomes readable and modifiable in transit','EXPOSED','Attacker on path can observe/alter unencrypted message'],
      ['Repair: HTTPS enforced and cleartext disabled','Cleartext regression rejected','BLOCKED','Manifest/network security configuration and endpoint TLS requirement']])

def simulate_power():
    rows=[
      ['Baseline always-awake','CPU high 8h',1000,70,30,360,'No idle batching; processor held awake'],
      ['DVFS enabled','CPU frequency adapts',1000,48,30,290,'CPU energy reduced; compute may take longer'],
      ['OS idle control','Doze / standby windows',80,14,6,175,'Network and jobs deferred during idle; app must tolerate delay'],
      ['App batching','Batch sensors and network',24,18,8,196,'Fewer radio wake-ups; batch latency increases'],
      ['Combined adaptive policy','DVFS + OS scheduling + batching',18,12,5,142,'Lowest modelled energy; reduced timeliness for non-urgent work'],
    ]
    write_csv('b5_power_techniques.csv',['policy','mechanism','wakeups_per_8h','cpu_energy_mAh','radio_energy_mAh','total_estimated_energy_mAh','interpretation'],rows)
    fig,ax=plt.subplots(figsize=(8,4.5)); names=[r[0] for r in rows]; energy=[r[5] for r in rows]; ax.bar(names,energy,edgecolor='black',color=['white','lightgray','white','lightgray','white'],hatch=['','//','..','xx','\\\\']); ax.set_ylabel('Estimated incremental energy (mAh / 8 h)'); ax.set_title('B5 – Modelled power-policy comparison'); ax.tick_params(axis='x',rotation=15); ax.grid(axis='y',linestyle=':',color='gray'); savefig(fig,'b5_power_comparison.png')
    # Stress test
    stress=[['Batched baseline',24,196,'normal batch windows'],['Partial wake lock retained',480,318,'Doze benefit reduced because CPU stays awake'],['Frequent exact alarms',360,274,'Alarm frequency defeats network coalescing'],['Corrected policy',18,142,'Release wake locks promptly; use deferrable jobs and sensor batching']]
    write_csv('b5_power_stress.csv',['scenario','wakeups_per_8h','estimated_energy_mAh','cause'],stress)
    fig,ax=plt.subplots(figsize=(7.5,4.5)); ax.bar([x[0] for x in stress],[x[2] for x in stress],edgecolor='black',color='white',hatch=['','//','..','xx']); ax.set_ylabel('Estimated energy (mAh / 8 h)'); ax.set_title('B5 – Stress cases that defeat power savings'); ax.tick_params(axis='x',rotation=14); ax.grid(axis='y',linestyle=':',color='gray'); savefig(fig,'b5_power_stress.png')

def policy_decision(battery,charging,network,motion,hot=False):
    if hot: return 180,900,'DEFER_UPLOAD', 'thermal-protection'
    if charging and network=='Wi-Fi': return 10,30,'UPLOAD_BATCH', 'charging-wifi'
    if battery<=15: return 300,1800,'DEFER_UNTIL_WIFI_OR_CHARGE','critical-battery'
    if battery<=25 and motion=='stationary': return 120,900,'BATCH_LTE','low-battery-stationary'
    if network=='NONE': return 60,None,'QUEUE_ONLY','offline'
    if network=='LTE' and motion=='moving': return 30,60,'BATCH_LTE','mobile-lte'
    return 60,300,'BATCH','default'

def simulate_tracking():
    scenarios=[
      ['Charging / Wi-Fi',95,True,'Wi-Fi','moving',False],
      ['80% battery / LTE moving',80,False,'LTE','moving',False],
      ['20% battery / LTE stationary',20,False,'LTE','stationary',False],
      ['Battery saver / LTE',14,False,'LTE','moving',False],
      ['No connectivity',55,False,'NONE','stationary',False],
      ['Device hot',50,False,'LTE','moving',True],
    ]
    rows=[]
    for name,batt,ch,net,motion,hot in scenarios:
        sample,upload,action,reason=policy_decision(batt,ch,net,motion,hot)
        samples=3600/sample
        uploads=0 if upload is None else 3600/upload
        # incremental telemetry model: 0.004 mAh/sample + 0.012 mAh/radio session + 0.05 mAh scheduler overhead
        energy=samples*.004+uploads*.012+.05
        encrypted='YES – AEAD before local queue; TLS for upload' if action!='QUEUE_ONLY' else 'YES – AEAD before local queue; no network'
        rows.append([name,batt,ch,net,motion,sample,upload if upload else 'NONE',action,reason,round(samples,1),round(uploads,1),round(energy,3),encrypted,'SIMULATED'])
    write_csv('b6_policy_scenarios.csv',['scenario','battery_percent','charging','network','motion','sampling_interval_s','upload_interval_s','upload_action','policy_reason','samples_per_hour','radio_sessions_per_hour','estimated_incremental_telemetry_mAh_per_hour','security','evidence_type'],rows)
    # Validation: manual compute same for three representative cases
    val=[]
    for idx in [0,2,4]:
        r=rows[idx]; manual=(3600/r[5])*.004+(0 if r[6]=='NONE' else 3600/float(r[6]))*.012+.05
        val.append([r[0],round(manual,3),r[11],round(r[11]-manual,6),'PASS' if abs(r[11]-manual)<1e-6 else 'CHECK'])
    write_csv('b6_validation.csv',['scenario','hand_calculated_mAh_per_hour','prototype_simulation_mAh_per_hour','difference','validation'],val)
    # Scalability: N records per device across fleet sizes
    scale=[]
    for records_per_device in [100,1000,10000]:
      for devices in [1,5,10,20]:
        total=records_per_device*devices
        wake=math.ceil(records_per_device/50)*devices
        mem=total*.8/1024 # MB, 0.8 KB per compact encrypted record
        energy=total*.004+wake*.012
        scale.append([records_per_device,devices,total,total,wake,round(mem,2),round(energy,3),round(energy/devices,3)])
    write_csv('b6_scalability.csv',['records_per_device','device_count','total_records','policy_evaluations','batched_wakeups','estimated_buffer_memory_mb','fleet_incremental_energy_mAh','per_device_incremental_energy_mAh'],scale)
    fig,ax=plt.subplots(figsize=(8,4.5)); rpd=[100,1000,10000]
    for devices,marker in [(1,'o'),(20,'s')]:
        vals=[next(r[6] for r in scale if r[0]==n and r[1]==devices) for n in rpd]
        ax.plot(rpd,vals,marker=marker,label=f'{devices} device(s)')
    ax.set_xscale('log'); ax.set_xlabel('Queued records per device'); ax.set_ylabel('Estimated fleet telemetry energy (mAh)'); ax.set_title('B6 – Scalability of batching policy'); ax.legend(); ax.grid(True,which='both',linestyle=':',color='gray'); savefig(fig,'b6_scalability.png')
    # Compare 10h always-on and adaptive scenarios
    always_per_hour=3600*.004+3600*.012+.05
    adaptive_rows=[]
    for r in rows:
        adaptive_rows.append([r[0],round(always_per_hour*10,2),round(r[11]*10,2),round((1-r[11]/always_per_hour)*100,1)])
    write_csv('b6_energy_vs_always_on.csv',['scenario','always_on_10h_mAh','adaptive_10h_mAh','modelled_reduction_percent'],adaptive_rows)
    fig,ax=plt.subplots(figsize=(8.5,4.5)); labels=[r[0] for r in adaptive_rows]; x=range(len(labels)); w=.38
    ax.bar([i-w/2 for i in x],[r[1] for r in adaptive_rows],w,label='Always-on baseline',edgecolor='black',color='white')
    ax.bar([i+w/2 for i in x],[r[2] for r in adaptive_rows],w,label='Adaptive policy',edgecolor='black',color='lightgray',hatch='//')
    ax.set_xticks(list(x),labels,rotation=14); ax.set_ylabel('Estimated incremental telemetry energy (mAh / 10 h)'); ax.set_title('B6 – Adaptive policy versus continuous sampling/upload'); ax.legend(); ax.grid(axis='y',linestyle=':',color='gray'); savefig(fig,'b6_adaptive_vs_baseline.png')
    # sample trace with six conditions
    write_csv('b6_policy_decision_trace.csv',['event','input','decision','security_action','reason'],[
      [1,'Charging + Wi-Fi','sample 10 s; upload every 30 s','encrypt local batch; TLS upload','bulk sync while externally powered'],
      [2,'LTE + moving + 80%','sample 30 s; upload every 60 s','encrypt local batch; TLS upload','movement needs fresher track'],
      [3,'LTE + stationary + 20%','sample 120 s; upload every 900 s','encrypt and queue','preserve battery; lower urgency'],
      [4,'Battery saver 14%','sample 300 s; defer','encrypt and queue','critical reserve; normal emergency override is separate'],
      [5,'No network','sample 60 s; queue only','encrypt before queue','no radio retries while offline'],
      [6,'Thermal high','sample 180 s; defer','encrypt and queue','limit heat and CPU/radio work']])

def main():
    simulate_os_states(); simulate_threading(); simulate_runtime(); simulate_security(); simulate_power(); simulate_tracking()
    print('SIMULATED OUTPUT – NOT A PHYSICAL DEVICE MEASUREMENT')
    print('Generated CSV files:',len(list(RES.glob('*.csv'))),'Figures:',len(list(FIG.glob('*.png'))))
    print('All figures and CSV values derive from deterministic assumptions in this script.')

if __name__=='__main__': main()

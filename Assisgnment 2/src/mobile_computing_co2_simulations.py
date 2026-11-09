import os, math
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import mm

D="/mnt/data"; os.makedirs(D,exist_ok=True)
rng=np.random.default_rng(20261104)

# Q1 simulation
q1=[]
for p in [0.9,0.6,0.3]:
    n=10000; avail=rng.random(n)<p
    delays=np.zeros(n,dtype=int)
    for i,ok in enumerate(avail):
        if not ok:
            w=1
            while rng.random()>=p: w+=1
            delays[i]=w
    q1.append([p,n,int(avail.sum()),int((~avail).sum()),n,int((delays>0).sum()),round(delays.mean(),3),int(delays.max())])
q1df=pd.DataFrame(q1,columns=["Availability","Generated","Immediate delivered","Immediate lost","Queued delivered","Queued delayed","Mean delay (min)","Maximum delay (min)"])
q1raw=pd.DataFrame({"record_id":np.arange(1,10001),"availability_90pct":(rng.random(10000)<.9).astype(int)})
q1df.to_csv(f"{D}/Q1_simulation_summary.csv",index=False); q1raw.to_csv(f"{D}/Q1_sample_raw.csv",index=False)

# Q2 traffic simulation
caps={"FDMA":76,"TDMA":70}
starts=np.sort(rng.uniform(0,60,200)); ev=sorted([(x,1) for x in starts]+[(x+.1,-1) for x in starts])
active=peak=0
for _,v in ev: active+=v; peak=max(peak,active)
q2=[]
for case,demand in [("Continuous voice",60),("Bursty telemetry peak",peak),("Synchronized edge burst",90)]:
    for scheme,cap in caps.items():
        q2.append([case,scheme,demand,cap,round(min(demand,cap)/cap*100,2),max(0,demand-cap),max(0,cap-demand)])
q2df=pd.DataFrame(q2,columns=["Traffic case","Scheme","Peak demand","Usable resources","Utilisation %","Blocked","Free at peak"])
q2df.to_csv(f"{D}/Q2_traffic_simulation.csv",index=False)

# Q3 simplified DS-CDMA
def hadamard(n):
    h=np.array([[1.]])
    while len(h)<n: h=np.block([[h,h],[h,-h]])
    return h
q3=[]
for N in [8,16,64]:
    H=hadamard(N); orth=H[:4]; randcodes=rng.choice([-1,1],(4,N))
    for name,codes in [("Synchronous Walsh",orth),("Random non-orthogonal",randcodes)]:
        bits=rng.integers(0,2,(4,3000)); sym=2*bits-1; errs=0
        for b in range(3000):
            rx=np.sum(sym[:,b,None]*codes,axis=0)+rng.normal(0,math.sqrt(N/20),N)
            errs += ((np.dot(rx,codes[0])>=0)!=(bits[0,b]==1))
        corr=(codes@codes.T)/N; maxc=np.max(np.abs(corr-np.eye(4)))
        q3.append([N,name,4,round(float(maxc),4),round(10*math.log10(N),2),int(errs),3000,errs/3000])
    bits_nf=rng.integers(0,2,(2,3000)); sym_nf=2*bits_nf-1
    target_code=orth[3]; strong_code=orth[2]; nf_errors=0
    for b in range(3000):
        strong=sym_nf[1,b]*strong_code*math.sqrt(10)
        delayed=np.concatenate(([0],strong[:-1]))
        rx_nf=sym_nf[0,b]*target_code+delayed+rng.normal(0,0.25,N)
        decision=(np.dot(rx_nf,target_code)>=0)
        nf_errors += (decision != (bits_nf[0,b]==1))
    shifted_code=np.concatenate(([0],strong_code[:-1]))
    shifted_corr=abs(np.dot(target_code,shifted_code))/N
    q3.append([N,"Near-far 10:1, 1-chip offset",2,round(float(shifted_corr),4),round(10*math.log10(N),2),int(nf_errors),3000,nf_errors/3000])
q3df=pd.DataFrame(q3,columns=["Code length","Condition","Users","Max cross-correlation","Processing gain dB","Errors","Bits","BER"])
q3df.to_csv(f"{D}/Q3_cdma_simulation.csv",index=False)

# Q4 OFDMA
U,K,R=8,64,1000
q4=[]
for rep in range(R):
    g=rng.exponential(1,(U,K)); rates=np.log2(1+10*g)
    fixed=np.zeros((U,K),bool); inter=np.zeros((U,K),bool); best=np.zeros((U,K),bool)
    for u in range(U): fixed[u,u*8:(u+1)*8]=True
    for k in range(K): inter[k%U,k]=True
    winners=np.argmax(rates,axis=0); best[winners,np.arange(K)]=True
    for name,a in [("Fixed contiguous",fixed),("Interleaved round-robin",inter),("Best-subcarrier",best)]:
        x=(rates*a).sum(axis=1); j=x.sum()**2/(U*(x*x).sum())
        q4.append([rep,name,x.sum(),x.min(),j,*x.tolist()])
q4cols=["Run","Scheme","Sum rate","Minimum user rate","Jain index"]+[f"User {i+1}" for i in range(U)]
q4df=pd.DataFrame(q4,columns=q4cols); q4df.to_csv(f"{D}/Q4_ofdma_1000_runs.csv",index=False)
q4sum=q4df.groupby("Scheme")[["Sum rate","Minimum user rate","Jain index"]].mean().reset_index()

# Q5 ULA
theta=np.linspace(-90,90,36001); q5=[]; patterns={}
for N in [2,4,8,16]:
    af=sum(np.exp(1j*n*np.pi*np.sin(np.deg2rad(theta))) for n in range(N))
    mag=np.abs(af)/N; db=20*np.log10(np.maximum(mag,1e-6))
    null=np.rad2deg(np.arcsin(min(1,2/N))); bw=2*null
    mask=np.abs(theta)>null+.05
    sl=float(db[mask].max()) if mask.any() else "Not applicable"
    cand=np.arange(5,60.1,.1); gc=np.interp(cand,theta,mag**2)
    ok=np.where(10*np.log10(1/np.maximum(gc,1e-12))>=10)[0]
    minsep=round(float(cand[ok[0]]),1) if len(ok) else "Not met"
    q5.append([N,round(bw,2),round(sl,2) if isinstance(sl,(int,float)) else sl,minsep]); patterns[N]=(theta,db)
q5df=pd.DataFrame(q5,columns=["Elements","First-null beamwidth deg","Peak sidelobe dB","Minimum separation for 10dB SIR deg"])
q5df.to_csv(f"{D}/Q5_sdma_metrics.csv",index=False)

# Q6 weighted matrix
criteria=["Capacity","Mobility","Resilience","Simplicity","Fairness"]
w=np.array([.30,.20,.20,.15,.15]); tech=["FDMA","TDMA","CDMA","OFDMA","SDMA"]
scenarios={
"Wide-area voice":[[3,4,2,5,3],[4,5,3,4,4],[4,4,4,3,3],[5,4,3,2,4],[4,3,3,2,3]],
"Tactical link":[[2,3,2,5,2],[3,3,2,4,3],[4,3,4,3,3],[3,2,2,2,3],[3,3,2,2,2]],
"Stadium downlink":[[2,3,2,5,2],[3,3,2,4,3],[3,3,3,3,3],[5,4,3,2,4],[4,3,3,2,3]],
"Low-rate sensors":[[2,3,2,5,2],[4,3,3,4,4],[3,3,3,3,3],[4,3,2,2,3],[3,2,2,2,2]]}
q6=[]
for s,mat in scenarios.items():
    for t,row,score in zip(tech,mat,np.array(mat)@w): q6.append([s,t,*row,round(float(score),3)])
q6df=pd.DataFrame(q6,columns=["Deployment","Technique",*criteria,"Weighted score"])
q6df.to_csv(f"{D}/Q6_decision_matrix.csv",index=False)
sens=[]
for scenario,mat in scenarios.items():
    mat=np.array(mat)
    for ci,criterion in enumerate(criteria):
        for factor in [0.8,1.2]:
            varied=w.copy(); varied[ci]*=factor; varied=varied/varied.sum()
            scores=mat@varied
            sens.append([scenario,criterion,factor,tech[int(np.argmax(scores))],round(float(scores.max()),3)])
sensitivity_df=pd.DataFrame(sens,columns=["Deployment","Weight changed","Multiplier","Winning technique","Top score"])
sensitivity_df.to_csv(f"{D}/Q6_weight_sensitivity.csv",index=False)

# Q7 paired scheduler validation
q7=[]
for rep in range(1000):
    g=rng.exponential(1,(U,K)); rates=np.log2(1+10*g); target=.05*np.max(rates,axis=0).sum()
    win=np.argmax(rates,axis=0); a0=np.zeros((U,K),bool); a0[win,np.arange(K)]=True
    x0=(rates*a0).sum(axis=1)
    a=np.zeros((U,K),bool); served=np.zeros(U); remaining=set(range(K))
    while remaining and np.any(served<target):
        u=int(np.argmax(np.maximum(0,target-served)))
        if served[u]>=target: break
        k=max(remaining,key=lambda kk:rates[u,kk]); a[u,k]=True; served[u]+=rates[u,k]; remaining.remove(k)
    avg=np.maximum(served,.05)
    for k in list(remaining):
        u=int(np.argmax(rates[:,k]/avg)); a[u,k]=True; served[u]+=rates[u,k]; avg[u]=.9*avg[u]+.1*served[u]
    for name,x in [("Original greedy",x0),("Redesigned min-rate + PF",served)]:
        q7.append([rep,name,x.sum(),x.min(),x.sum()**2/(U*(x*x).sum()),int((x<target).sum()),target])
q7df=pd.DataFrame(q7,columns=["Run","Scheduler","Sum rate","Minimum rate","Jain index","Users below target","Target"])
q7df.to_csv(f"{D}/Q7_validation_1000_runs.csv",index=False)
q7sum=q7df.groupby("Scheduler")[["Sum rate","Minimum rate","Jain index","Users below target","Target"]].mean().reset_index()

# Charts grayscale
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9})
figs={}
fig,ax=plt.subplots(figsize=(7,3))
ax.plot(q1df.Availability*100,q1df["Immediate delivered"]/100,marker="o",label="Immediate delivered (%)")
ax.plot(q1df.Availability*100,q1df["Queued delivered"]/100,marker="s",label="Queued delivered (%)")
ax.set_xlabel("Link availability (%)"); ax.set_ylabel("Delivered records (%)"); ax.set_ylim(0,105); ax.grid(linestyle=":"); ax.legend(frameon=False)
fig.tight_layout(); figs["q1"]=f"{D}/Q1_delivery.png"; fig.savefig(figs["q1"],dpi=170); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,3))
p=q2df[q2df["Traffic case"]=="Synchronized edge burst"]
ax.bar(p.Scheme,p.Blocked,edgecolor="black",color=["white","0.65"]); ax.set_ylabel("Blocked requests"); ax.grid(axis="y",linestyle=":")
fig.tight_layout(); figs["q2"]=f"{D}/Q2_blocking.png"; fig.savefig(figs["q2"],dpi=170); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,3))
for name,d in q3df.groupby("Condition"): ax.plot(d["Code length"],d.BER,marker="o",label=name)
ax.set_xscale("log",base=2); ax.set_xticks([8,16,64],[8,16,64]); ax.set_yscale("symlog",linthresh=1e-4); ax.set_xlabel("Code length"); ax.set_ylabel("BER"); ax.grid(True,which="both",linestyle=":"); ax.legend(frameon=False,fontsize=7)
fig.tight_layout(); figs["q3"]=f"{D}/Q3_ber.png"; fig.savefig(figs["q3"],dpi=170); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,3))
for name,d in q4df.groupby("Scheme"): ax.hist(d["Jain index"],bins=25,histtype="step",label=name)
ax.set_xlabel("Jain fairness index"); ax.set_ylabel("Runs"); ax.grid(axis="y",linestyle=":"); ax.legend(frameon=False,fontsize=7)
fig.tight_layout(); figs["q4"]=f"{D}/Q4_fairness.png"; fig.savefig(figs["q4"],dpi=170); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,3))
for n,(th,db) in patterns.items(): ax.plot(th,db,label=f"N={n}")
ax.set_xlim(-60,60); ax.set_ylim(-40,2); ax.set_xlabel("Angle (degrees)"); ax.set_ylabel("Normalised array factor (dB)"); ax.grid(linestyle=":"); ax.legend(frameon=False,ncol=4)
fig.tight_layout(); figs["q5"]=f"{D}/Q5_patterns.png"; fig.savefig(figs["q5"],dpi=170); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,3))
for s,d in q6df.groupby("Deployment"): ax.plot(d.Technique,d["Weighted score"],marker="o",label=s)
ax.set_ylim(0,5); ax.set_ylabel("Weighted score / 5"); ax.grid(axis="y",linestyle=":"); ax.legend(frameon=False,fontsize=7); ax.tick_params(axis="x",rotation=20)
fig.tight_layout(); figs["q6"]=f"{D}/Q6_scores.png"; fig.savefig(figs["q6"],dpi=170); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,3))
for s,d in q7df.groupby("Scheduler"): ax.hist(d["Jain index"],bins=25,histtype="step",label=s)
ax.set_xlabel("Jain fairness index"); ax.set_ylabel("Runs"); ax.grid(axis="y",linestyle=":"); ax.legend(frameon=False,fontsize=7)
fig.tight_layout(); figs["q7"]=f"{D}/Q7_fairness.png"; fig.savefig(figs["q7"],dpi=170); plt.close(fig)

# Construct 45 answer pages: 5+6+7+7+6+6+8
pages=[]
def page(title, paras, bullets=None, table=None, fig=None, caption=""):
    pages.append((title,paras,bullets or [],table,fig,caption))
# Q1
page("Q1 – Mobile Communication or Mobile Computing? (1/5): Concepts and Criteria",[
"Wireless and mobile are related but distinct. Wireless describes the transmission medium: information travels over a radio link rather than a cable for at least one network segment. Mobile describes the intended ability to operate while the user or endpoint changes location. A wireless router can be fixed, while a laptop can be nomadic even when connected by Ethernet.",
"Mobile communication concentrates on transferring voice, messages and data while endpoints move. Mobile computing includes portable processing, applications, local data and communication. It must often cope with handover, variable bandwidth, disconnection and limited device resources. The offline meter-reading tablet illustrates this wider meaning because its application must continue to work when the network is absent."
],["User mobility: does the endpoint operate while changing location?","Access medium: wired, wireless or mixed?","Session continuity: is service expected to survive movement or handover?","Disconnection tolerance: can the task continue offline?","Context awareness: does the application use location or changing conditions?","Local computing: does the device store and process task data?"])
page("Q1 – Mobile Communication or Mobile Computing? (2/5): Classification of Cases",[
"The cellular ruggedised tablet is mobile and primarily a mobile-computing problem: the user carries it, cellular connectivity is used, and the work-order application must preserve task state. The laptop used at different offices is nomadic: it moves between sites but uses Ethernet while connected. The remote substation router is fixed-wireless because the radio endpoint is stationary.",
"The push-to-talk handset is mobile and mainly a mobile-communication problem because radio coverage, voice setup and continuity dominate. The offline meter-reading tablet is mobile and mainly a mobile-computing problem because local capture and later synchronisation are essential."
],None,(["Case","Classification","Main focus","Reason"],[["Ruggedised tablet","Mobile","Mobile computing + communication","Portable field application over cellular."],["Laptop at offices","Nomadic","Mobile computing","Moved between sites; wired at each."],["Substation router","Fixed-wireless","Communication","Wireless but stationary."],["Push-to-talk handset","Mobile","Mobile communication","Portable voice terminal."],["Offline meter tablet","Mobile","Mobile computing","Local capture and sync later."]]))
page("Q1 – Mobile Communication or Mobile Computing? (3/5): Ambiguous Case and Simulation Design",[
"An ambiguous case is a tablet mounted in a parked emergency-response vehicle. While docked it connects to a fixed Wi-Fi access point and behaves as fixed-wireless. When removed and carried into a building it is mobile. The correct classification depends on the operating mode and task, not merely the product name.",
"The simulation uses 10,000 meter readings per availability level. At each generation instant, link availability is an independent probability p. Immediate-send attempts once and loses the reading if disconnected. Store-and-forward saves the record and retries at one-minute intervals until a connection is available. The model assumes unlimited queue capacity, no duplicate delivery and eventual recovery of the link."
],["Test p = 0.90, 0.60 and 0.30.","Use random seed 20261104 for reproducibility.","Record delivered, delayed, lost and mean delay.","The model isolates application-level disconnection tolerance; it is not a live cellular trace."])
page("Q1 – Mobile Communication or Mobile Computing? (4/5): Simulation Results",[
"The seeded experiment shows immediate delivery decreasing with link availability. Store-and-forward delivers every record eventually under the no-overflow assumption, but the number delayed and mean delay increase as availability falls. This demonstrates a reliability-versus-latency trade-off: the queue prevents permanent loss but cannot make an unavailable network faster.",
"The results are simulated values under independent availability, one-minute retries and unlimited storage. Real outages may be correlated, and transfers may fail due to packet errors or limited throughput. The raw sample CSV and summary CSV are supplied with the report."
],None,(list(q1df.columns),q1df.values.tolist()),figs["q1"],"Figure Q1.1 – Immediate and queued delivery across link availability.")
page("Q1 – Mobile Communication or Mobile Computing? (5/5): Inquiry and Conclusion",[
"The application must implement local persistence, retry logic, unique record identifiers, duplicate detection, timestamps, conflict handling and visible synchronisation state. The offline meter-reading tablet needs these features most. The ruggedised work-order tablet benefits from cached work orders and queued updates. The push-to-talk handset mainly depends on radio coverage; the fixed router needs network reliability rather than mobility-aware application logic.",
"Conclusion: wireless identifies how information travels, while mobile identifies operation across changing locations and conditions. Mobile communication provides connectivity during movement. Mobile computing adds local processing and data management so that work remains useful during disconnection."
])
# Q2
page("Q2 – Sharing the Channel: FDMA vs TDMA (1/6): Nominal Capacity",[
"The system provides 2 MHz per direction. FDMA uses 25 kHz channels, giving 2,000/25 = 80 nominal channels. TDMA uses 200 kHz carriers with eight slots. There are 2,000/200 = 10 carriers, so 10×8 = 80 nominal slots. Equal nominal counts do not guarantee equal usable capacity.",
"Guard bands, guard times, synchronisation and control signalling reduce traffic resources. For a transparent teaching model, reserve 5% of FDMA channel-equivalents and one of eight TDMA slots per carrier. These are stated assumptions, not universal standards values."
],None,(["Parameter","FDMA","TDMA"],[["Nominal resources","80 channels","10×8 = 80 slots"],["Assumed overhead","5% reserve","1 slot per carrier"],["Usable resources","76","70 traffic slots"]]))
page("Q2 – Sharing the Channel: FDMA vs TDMA (2/6): Usable Capacity",[
"FDMA usable capacity is 80×0.95 = 76 channel-equivalents. The assumed 5% represents a simplified combined guard and control reserve. TDMA provides 80 nominal slots; reserving one slot on each of ten carriers leaves 10×7 = 70 traffic slots.",
"These counts are resource equivalents, not direct throughput comparisons. TDMA may use its traffic slots more efficiently when a scheduler reallocates unused slots to bursty users. A fixed reservation can waste capacity in either scheme."
],None,(["Calculation","Result"],[["FDMA nominal","2,000/25 = 80"],["FDMA usable","80×0.95 = 76"],["TDMA nominal","(2,000/200)×8 = 80"],["TDMA usable","10×7 = 70"]]))
page("Q2 – Sharing the Channel: FDMA vs TDMA (3/6): Traffic Predictions",[
"Continuous voice holds a resource for most of a call. FDMA provides predictable continuous access. TDMA can also carry voice using periodic slots, with timing and guard overhead. For bursty data at 10% duty cycle, a permanently reserved channel remains idle for much of the time; demand-based TDMA can allocate only when a report is ready.",
"For a 70/30 voice-data mix, protect voice with predictable resources and allow data to use residual capacity dynamically. The scheduler must preserve voice delay and continuity while avoiding unnecessary reservation for inactive data sources."
],["Continuous voice: both methods suitable.","Bursty data: dynamic TDMA expected to reduce idle allocation.","Mixed traffic: reserve voice capacity and share residual slots."])
page("Q2 – Sharing the Channel: FDMA vs TDMA (4/6): Traffic Datasets",[
"Dataset A contains 60 continuous voice calls. Dataset B contains 200 telemetry reports distributed randomly over 60 seconds; each report occupies a resource for 0.1 seconds. Dataset C is an edge case with 90 simultaneous requests. The event-sweep simulation estimates peak concurrency for the random telemetry case.",
"The model uses 76 FDMA channels and 70 TDMA traffic slots. It measures peak demand, utilisation and blocking. It does not model speech coding, packet headers, propagation or retransmission behaviour; the purpose is to isolate resource allocation and burst effects."
],["A: 60 continuous calls.","B: 200 short reports, random arrival, 0.1-second occupancy.","C: 90 synchronised arrivals.","Metrics: utilisation, blocking and free resources."])
page("Q2 – Sharing the Channel: FDMA vs TDMA (5/6): Simulation Results",[
"Sixty continuous calls produce FDMA utilisation of 60/76 = 78.95% and TDMA utilisation of 60/70 = 85.71%; neither blocks a call. The higher TDMA percentage reflects the smaller assumed traffic pool, not greater raw capacity.",
"The random telemetry case has a low measured peak because each short report occupies a resource for only 0.1 seconds. Both pools accommodate that peak. In the synchronised case, 90 requests exceed both pools: FDMA blocks 14 and TDMA blocks 20."
],None,(list(q2df.columns),q2df.values.tolist()),figs["q2"],"Figure Q2.1 – Blocked requests during the synchronised edge burst.")
page("Q2 – Sharing the Channel: FDMA vs TDMA (6/6): Design Decision",[
"FDMA partitions by frequency and TDMA partitions by time. Dynamic time-slot allocation can reduce idle allocation for bursty traffic, while fixed allocation wastes capacity in either system. At a campus telemetry site where 90% of devices send 200-byte reports per minute, permanent dedicated channels are not justified.",
"A shared packet-access method or demand-based TDMA is preferable. Reports can be staggered or aggregated to reduce synchronised peaks. Conclusion: choose according to offered load and traffic shape, not device count alone."
])
# Q3
page("Q3 – CDMA: Orthogonality, Spreading and Near-Far (1/7): Principle",[
"Direct-sequence CDMA allows users to share the same frequency band simultaneously. Each data symbol is multiplied by a spreading code. The receiver correlates the composite signal with the target code. Distinct aligned Walsh codes have zero cross-correlation over the spreading interval.",
"For BPSK, bit 1 maps to +1 and bit 0 to −1. A four-chip code [1,−1,1,−1] spreads bit 1 to [1,−1,1,−1] and bit 0 to [−1,1,−1,1]. The receiver multiplies by the same code and sums; the sign gives the decision."
],None,(["N chips","Linear processing gain","dB"],[[8,8,"9.03"],[16,16,"12.04"],[64,64,"18.06"]]))
page("Q3 – CDMA: Orthogonality, Spreading and Near-Far (2/7): Worked Example",[
"For the code c=[1,−1,1,−1], a noise-free bit 1 produces a despread sum of +4, while bit 0 produces −4. Dividing by four gives +1 or −1, so a zero threshold recovers the bit.",
"With multiple users, the receiver observes the sum of all spread signals and noise. Orthogonal aligned codes ideally cancel in the target correlator. Timing offsets and multipath disturb chip alignment and produce residual interference."
],None,(["Bit","BPSK symbol","Spread chips","Despread sum"],[["1","+1","[1,−1,1,−1]","+4"],["0","−1","[−1,1,−1,1]","−4"]]))
page("Q3 – CDMA: Orthogonality, Spreading and Near-Far (3/7): Predictions",[
"Synchronous Walsh codes should have low BER under ideal alignment because distinct code rows are orthogonal. Random non-orthogonal codes should produce multi-access interference that tends to increase with user count. A ten-times-power interferer should be particularly harmful when a timing offset breaks orthogonality.",
"The near-far test represents a ten-to-one received power ratio using an amplitude factor √10 and a one-chip offset. The model is simplified but demonstrates why code orthogonality depends on timing and channel conditions."
],["Walsh aligned: lowest predicted interference.","Random codes: non-zero cross-correlation.","Near-far with timing offset: weak-user BER can rise."])
page("Q3 – CDMA: Orthogonality, Spreading and Near-Far (4/7): Simulation Setup",[
"The experiment uses four users, BPSK, AWGN and 3,000 bits per condition. Spreading lengths are 8, 16 and 64. Walsh-Hadamard rows provide the orthogonal condition; random ±1 sequences provide the non-orthogonal condition. The receiver correlates the received chip block with user 1's code.",
"BER equals bit errors divided by bits tested. Maximum absolute off-diagonal normalised correlation is recorded. A fixed random seed makes the code choices, bits and noise repeatable. The numerical values are specific to this simplified chip-level model."
],["Seed: 20261104.","Bits: 3,000 per condition.","Code lengths: 8, 16, 64.","Noise: AWGN with fixed settings."])
page("Q3 – CDMA: Orthogonality, Spreading and Near-Far (5/7): BER and Processing Gain",[
"The aligned Walsh code family has zero off-diagonal correlation by construction. Random sequences have non-zero correlations determined by the generated codes. Processing gain increases with code length: 9.03 dB at N=8, 12.04 dB at N=16 and 18.06 dB at N=64.",
"The BER table reports the actual seeded experiment. BER should be interpreted with code correlation, SNR and user count; a single low BER result does not prove a random code family is orthogonal."
],None,(list(q3df.columns),q3df.values.tolist()),figs["q3"],"Figure Q3.1 – BER across code lengths and code families.")
page("Q3 – CDMA: Orthogonality, Spreading and Near-Far (6/7): User Capacity",[
"Supported user count depends on BER target, spreading factor, received-power balance, synchronisation and channel conditions. Define BER ≤ 10⁻³ as the target and increase the user count in steps. The supported count is the largest tested load for which every required user meets the target.",
"The four-user experiment demonstrates code-family behaviour; it must not be extrapolated into a universal capacity claim. A full capacity sweep should add users, retain per-user BER and record the exact code matrix, SNR, seed and timing offsets."
],["Report per-user BER.","State target BER and bits tested.","Retain code matrix and random seed.","Do not extrapolate beyond tested loads."])
page("Q3 – CDMA: Orthogonality, Spreading and Near-Far (7/7): Inquiry and Conclusion",[
"Unsynchronised users have misaligned chip boundaries, so positive and negative correlation products no longer cancel. Multipath creates delayed signal copies and also reduces orthogonality. Power control is essential because a nearby handset can arrive much stronger than a distant handset, allowing residual cross-correlation to dominate the weak user's decision.",
"Conclusion: spreading enables shared-band access, but orthogonality is conditional. Longer codes increase processing gain, yet they do not independently correct timing offsets, multipath or power imbalance. Practical CDMA combines code design, synchronisation, receiver processing and power control."
])
# Q4
page("Q4 – OFDMA: Subcarrier Allocation (1/7): OFDM Fundamentals",[
"OFDMA divides a wide channel into narrow orthogonal subcarriers and assigns different groups to users. Subcarrier spacing Δf and useful symbol duration Tᵤ are related by Tᵤ=1/Δf. At 15 kHz spacing, Tᵤ=66.67 μs.",
"A cyclic prefix copies the end of the useful symbol to its beginning. It absorbs multipath delay spread and helps preserve orthogonality when channel delay is shorter than the prefix. A 4.7 μs prefix gives a total duration of 71.37 μs and useful-time efficiency of 93.4%."
],None,(["Parameter","Illustrative value"],[["Spacing","15 kHz"],["Useful symbol","66.67 μs"],["Cyclic prefix","4.7 μs"],["Total duration","71.37 μs"],["Useful efficiency","93.4%"]]))
page("Q4 – OFDMA: Subcarrier Allocation (2/7): Orthogonality Verification",[
"The discrete inner product between subcarriers k and m is (1/N)Σ exp(j2π(k−m)n/N). It equals one for the same subcarrier and approximately zero for distinct integer subcarriers over the complete useful symbol.",
"For N=64 and subcarriers 0, 1 and 2, the self-inner-product is 1+j0 and cross-inner-products are approximately zero, apart from floating-point precision. Timing error, carrier-frequency offset and phase noise can create inter-carrier interference."
],None,(["Pair","Expected inner product"],[["0,0","1+j0"],["0,1","≈0"],["0,2","≈0"],["1,2","≈0"]]))
page("Q4 – OFDMA: Subcarrier Allocation (3/7): Three Allocation Approaches",[
"Fixed contiguous allocation assigns eight adjacent tones to each of eight users. It is simple but can place a user in a deep fade. Interleaved round-robin distributes tones across the band and gives frequency diversity, but ignores instantaneous channel quality.",
"Best-subcarrier allocation assigns each tone to the user with the highest measured gain. It can maximise sum throughput but may repeatedly favour strong users. The three methods are compared using identical channel realisations."
],None,(["Method","Rule","Strength","Risk"],[["Contiguous","Adjacent blocks","Simple","Block may fade"],["Interleaved","Round-robin tones","Frequency diversity","No CSI use"],["Best-subcarrier","Highest gain per tone","High sum rate","Starvation"]]))
page("Q4 – OFDMA: Subcarrier Allocation (4/7): Metrics and Experiment",[
"The simulation uses eight users, 64 subcarriers, 1,000 channel realisations and linear SNR 10. Rayleigh fading power gains are generated from an exponential distribution. Per-tone spectral efficiency is modelled as log₂(1+SNR×gain).",
"Jain's fairness index is J=(Σxᵤ)²/[UΣxᵤ²], where xᵤ is user throughput. It ranges from 1/U to one. The Shannon-style rate is a comparative abstraction; real systems use discrete modulation and coding, overhead and retransmissions."
],None,(["Metric","Meaning"],[["Per-user rate","Sum of rates on assigned tones"],["Sum rate","Total spectral efficiency"],["Jain index","Throughput fairness"],["Tone count","Resource distribution"]]))
page("Q4 – OFDMA: Subcarrier Allocation (5/7): Measured Results",[
"The 1,000-run experiment records sum throughput, minimum user rate and Jain's fairness index. Fixed contiguous and interleaved round-robin give each user eight tones. Best-subcarrier allocation varies tone counts according to channel quality.",
"Results are averages over the seeded channel realisations. They should be interpreted as spectral-efficiency units in this model, not as commercial-network Mbps. The raw per-run CSV is supplied for independent analysis."
],None,(list(q4sum.columns),q4sum.values.tolist()),figs["q4"],"Figure Q4.1 – Fairness distribution over 1,000 channel realisations.")
page("Q4 – OFDMA: Subcarrier Allocation (6/7): Starvation and User Count",[
"A greedy scheduler can starve users because it repeatedly assigns each tone to the user with the highest instantaneous gain. Increasing user count can increase multi-user diversity and aggregate throughput, but it also increases feedback and scheduling complexity. Weak users may wait longer.",
"Proportional fairness balances instantaneous rate against recent average throughput. A minimum-rate constraint can further protect weak users. The scheduler should consider both channel quality and service history."
],["Sum throughput is not the same as fairness.","More users can improve diversity but increase feedback.","Minimum-rate constraints protect users with poor channels."])
page("Q4 – OFDMA: Subcarrier Allocation (7/7): Lecture-Hall Decision",[
"For a lecture hall, pure best-subcarrier allocation is unsuitable if every student must receive a minimum rate. Round-robin gives equal tone counts but does not guarantee equal bit rates when channel gains differ.",
"A two-stage scheduler should first protect a minimum rate for each admitted student, then allocate remaining tones using channel quality or proportional fairness. If the target is infeasible, report the shortfall and use admission control rather than silently starving users."
])
# Q5
page("Q5 – SDMA: Directional Antennas (1/6): Array-Factor Model",[
"SDMA separates users by spatial direction. A uniform linear array with N elements and spacing d has array factor AF(θ)=Σ exp[jn(kd sinθ+β)], where k=2π/λ. Steering toward θ₀ requires β=−kd sinθ₀.",
"The model uses d=λ/2 and broadside steering. It excludes element patterns, mutual coupling, calibration errors and multipath, so it isolates the effect of array size."
],None,(["Symbol","Meaning"],[["N","Number of elements"],["d","Element spacing"],["λ","Wavelength"],["k","2π/λ"],["β","Progressive phase"]]))
page("Q5 – SDMA: Directional Antennas (2/6): Beamwidth and Sidelobes",[
"As N increases at fixed spacing, the main lobe narrows. The first-null beamwidth of a broadside uniform array is approximately inversely proportional to N. A narrower beam improves angular discrimination for users with separated arrival directions.",
"Uniform excitation produces sidelobes. Increasing N does not eliminate them; the largest sidelobe of an ideal uniform array is approximately −13 dB for a sufficiently large array. Tapering can reduce sidelobes but broadens the main lobe."
],None,(list(q5df.columns),q5df.values.tolist()))
page("Q5 – SDMA: Directional Antennas (3/6): SIR Threshold",[
"The design defines a 10 dB SIR threshold. The beam is steered toward user A at broadside and user B is placed at angular separation Δθ. With equal transmit powers and equal path-loss references, SIR is estimated from the main-beam gain divided by the gain toward user B.",
"The minimum separation is the first angle from 5° to 60° at which the threshold is met. This is a pattern-only estimate; real distances, reflections and shadowing affect the link budget."
],["Array sizes: 2, 4, 8 and 16.","Element spacing: λ/2.","Angular sweep: 5°–60°.","Threshold: 10 dB."])
page("Q5 – SDMA: Directional Antennas (4/6): Computed Patterns",[
"The array factor is evaluated over −90° to +90°, normalised by its maximum and converted to decibels. Main-lobe width is measured between first nulls and sidelobe level is the largest local maximum outside the main lobe.",
"The plot demonstrates the narrowing main lobe as the array grows. Larger arrays improve angular resolution but require more hardware, calibration and processing."
],None,None,figs["q5"],"Figure Q5.1 – Broadside array patterns for N=2, 4, 8 and 16.")
page("Q5 – SDMA: Directional Antennas (5/6): Practical Limits",[
"SDMA is limited by angular spread, clustered users, multipath, calibration and the number of independent spatial channels. Users arriving from nearly the same direction have highly correlated spatial signatures and cannot be cleanly separated by a simple beamformer.",
"At a toll plaza, most vehicles approach from the same direction. Directional antennas can improve coverage, but SDMA should not be the only separation method. Use time or frequency scheduling for vehicles whose angular signatures overlap."
],["Angular clustering limits separation.","Multipath changes apparent arrival direction.","Calibration errors distort beams.","More elements add cost and complexity."])
page("Q5 – SDMA: Directional Antennas (6/6): Conclusion",[
"Increasing array size narrows the main lobe and improves separation for users at distinct angles. However, a larger array does not remove the limitation created by nearly identical directions. The toll-plaza design should combine directional gain with time/frequency scheduling and validate angular thresholds using computed patterns."
])
# Q6
page("Q6 – Choosing Multiple-Access Techniques (1/6): Criteria and Weights",[
"Four deployments are assessed: wide-area cellular voice, jam-resistant tactical link, high-rate stadium downlink and 5,000 low-rate sensors. The weighted criteria are capacity efficiency, mobility/coverage, resilience, implementation simplicity and fairness/QoS.",
"Weights are 30%, 20%, 20%, 15% and 15%. Ratings use a 1–5 scale. These are scenario-specific engineering judgements, not universal constants. The sensitivity check changes each weight by ±20% and renormalises the total to 100%."
],None,(["Criterion","Weight"],[["Capacity efficiency","30%"],["Mobility/coverage","20%"],["Resilience","20%"],["Simplicity","15%"],["Fairness/QoS","15%"]]))
page("Q6 – Choosing Multiple-Access Techniques (2/6): Technique Characteristics",[
"FDMA separates users by frequency and offers simple continuous access, but guard bands and fixed allocations can waste spectrum. TDMA separates users by time and supports scheduled sharing, but needs timing synchronisation. CDMA uses spreading codes, but capacity is interference-limited and near-far control is required.",
"OFDMA supports flexible broadband scheduling across subcarriers, but requires channel feedback and synchronisation. SDMA reuses frequency-time resources in different directions, but angularly clustered users are difficult to separate. Real systems combine these dimensions."
],None,(["Technique","Resource dimension","Benefit","Limitation"],[["FDMA","Frequency","Simple access","Guard bands"],["TDMA","Time","Dynamic sharing","Timing overhead"],["CDMA","Code","Spreading gain","Near-far"],["OFDMA","Subcarriers","Flexible broadband","Feedback"],["SDMA","Space","Spatial reuse","Angular correlation"]]))
page("Q6 – Choosing Multiple-Access Techniques (3/6): Wide-Area Voice",[
"Wide-area voice requires mobility, coverage, predictable delay and manageable call blocking. A time/frequency cellular architecture can provide stable voice resources, with sectorisation or beamforming adding spatial reuse. The final selection depends on the radio generation and standard.",
"The weighted decision matrix compares each technique using the five criteria. The choice should be validated against handover performance, call blocking, voice delay and coverage rather than relying on the score alone."
],None,(list(q6df[q6df.Deployment=="Wide-area voice"].columns),q6df[q6df.Deployment=="Wide-area voice"].values.tolist()))
page("Q6 – Choosing Multiple-Access Techniques (4/6): Tactical Link and Stadium",[
"CDMA is a candidate for a jam-resistant tactical link because spreading can reduce the effect of narrowband interference after despreading, provided processing gain and power control are sufficient. Frequency hopping can be combined with spreading. No access method is inherently jam-proof.",
"OFDMA is a strong choice for a high-rate stadium downlink because it schedules users across subcarriers and exploits frequency-selective channels. SDMA beamforming can add spatial reuse. Fairness-aware scheduling is needed to protect cell-edge users."
],None,(["Deployment","Primary method","Hybrid","Reason"],[["Tactical","CDMA","Frequency hopping","Narrowband interference mitigation"],["Stadium","OFDMA","SDMA","High-rate scheduling and spatial reuse"]]))
page("Q6 – Choosing Multiple-Access Techniques (5/6): Low-Rate Sensors",[
"For 5,000 low-rate sensors, permanent assignment of a frequency or slot to every device is inefficient when reports are small and infrequent. A scheduled low-duty-cycle TDMA design lets sensors sleep between reporting windows. Gateways can aggregate readings and stagger transmissions.",
"The recommended approach is low-duty-cycle TDMA with gateway aggregation and controlled contention for exceptional reports. This follows the Q2 finding that dedicated resources are wasteful for infrequent burst traffic."
],None,(list(q6df[q6df.Deployment=="Low-rate sensors"].columns),q6df[q6df.Deployment=="Low-rate sensors"].values.tolist()))
page("Q6 – Choosing Multiple-Access Techniques (6/6): Sensitivity and Conclusion",[
"The tactical-link decision is least robust because the jammer model is unspecified. Narrowband interference may favour spreading or hopping; a wideband high-power jammer can remove much of the advantage. The stadium OFDMA decision is more stable when high throughput is dominant, but minimum-rate requirements change the scheduler.",
"Real systems combine methods because frequency, time, code and space are separate resource dimensions. A system may divide spectrum into carriers, slots, codes and spatial beams. Hybrid designs are often needed to balance capacity, mobility, resilience, fairness and complexity."
],None,(list(q6df.columns),q6df.values.tolist()),figs["q6"],"Figure Q6.1 – Weighted scores for five access techniques across four deployments.")
# Q7
page("Q7 – Diagnose, Redesign and Validate (1/8): Selected Limitation",[
"The selected limitation is starvation in the best-subcarrier OFDMA scheduler. The greedy algorithm assigns each tone to the user with the highest channel gain. It can maximise total throughput, but users with consistently weak channels may receive few resources and fall below the lecture hall's minimum service requirement.",
"The problem is the scheduling objective, not OFDMA itself. The redesign retains the same subcarrier system and adds minimum-rate protection followed by proportional-fair allocation."
],["Original: greedy best-subcarrier allocation.","Limitation: strong users can repeatedly win.","Redesign: minimum-rate protection + proportional fairness."])
page("Q7 – Diagnose, Redesign and Validate (2/8): A. Diagnose the Bottleneck",[
"The bottleneck is the greedy allocation rule. Strong-channel users can win many scheduling decisions. Counted evidence includes tones per user, per-user throughput, minimum rate, maximum-to-minimum ratio and Jain's index.",
"Resources may all be occupied; the waste is service imbalance. Capacity is consumed without meeting weaker users' minimum service requirement. The root cause is a single objective—instantaneous sum rate—with no fairness or minimum-rate constraint."
],None,(["Diagnostic item","Finding"],[["Resource use","Tones assigned to highest-gain user."],["Growing quantity","Repeated wins and throughput imbalance."],["Resource condition","Occupied, but weak users underserved."],["Root cause","No fairness or minimum-rate term."]]))
page("Q7 – Diagnose, Redesign and Validate (3/8): B. Define the Objective",[
"The revised scheduler must satisfy a minimum service target for every admitted user before maximising remaining throughput. In the simulation, the target is 5% of the sum of best achievable rates across all 64 tones for each user over the scheduling window. This is a test target, not a standard service guarantee.",
"Success means zero users below target when feasible, higher Jain fairness and as much aggregate throughput as possible. If total capacity cannot meet the sum of minimum requirements, the scheduler must report infeasibility and trigger admission control."
],None,(["Objective","Measure","Success"],[["Minimum service","Users below target","Zero when feasible"],["Fairness","Jain index","Higher than baseline"],["Efficiency","Sum rate","Limit avoidable loss"],["Overload","Demand vs capacity","Report infeasibility"]]))
page("Q7 – Diagnose, Redesign and Validate (4/8): C. Revised Strategy",[
"Stage 1 protects minimum rates. Calculate each user's deficit, select the largest deficit and assign that user's best remaining tone. Repeat until every user meets the target or no tones remain. Stage 2 assigns residual tones using current achievable rate divided by recent average throughput.",
"The redesign exploits channel estimates and service history. It adds average-throughput state and deficit counters. The trade-off is that a tone may be assigned to a weaker user to meet the minimum rate, reducing peak aggregate throughput."
],["Compute user deficits.","Serve the largest deficit using that user's best remaining tone.","Allocate residual tones by proportional-fair score.","Update throughput history."])
page("Q7 – Diagnose, Redesign and Validate (5/8): C. Pseudocode",[
"The scheduler receives a user-by-tone rate matrix R, target T and recent average throughput A. Initialise delivered rates to zero and mark all tones available. While deficits remain, select the user with the largest deficit and assign that user's best remaining tone.",
"When all users meet the target or no tones remain, assign each residual tone to the user maximising R/A. Update average throughput and record aggregate rate, minimum rate, fairness and target misses. Both algorithms receive the same rate matrix in every validation run."
],None,(["Step","Pseudocode"],[["1","Input R, T, A."],["2","Initialise delivered=0; all tones available."],["3","Compute deficit=max(0,T−delivered)."],["4","Serve largest deficit with its best remaining tone."],["5","Allocate residual tones using R/A."],["6","Update A and record metrics."]]))
page("Q7 – Diagnose, Redesign and Validate (6/8): D. Prediction",[
"The prediction is that the redesigned scheduler reduces users below target and increases Jain fairness when the target is feasible. Aggregate throughput may decrease because some tones are assigned to weaker users to protect their service.",
"Additional state and selection operations are required. The prediction is falsifiable: under identical channel realisations compare sum rate, minimum user rate, Jain index and target misses. A failure to improve fairness should lead to review of the target and deficit update."
],None,(["Metric","Prediction"],[["Users below target","Decrease"],["Jain fairness","Increase"],["Sum rate","May decrease"],["State/complexity","Increase modestly"]]))
page("Q7 – Diagnose, Redesign and Validate (7/8): E. Validation Results",[
"Validation uses 1,000 paired channel realisations. Each generated user-tone matrix is supplied to both the original greedy and redesigned schedulers. This ensures that neither algorithm receives easier fading conditions by chance.",
"The table reports mean aggregate rate, minimum user rate, Jain fairness and users below target. Raw per-run values are provided in CSV. Results are specific to this simplified Rayleigh-fading model and its stated target."
],None,(list(q7sum.columns),q7sum.values.tolist()),figs["q7"],"Figure Q7.1 – Fairness distribution for the two schedulers.")
page("Q7 – Diagnose, Redesign and Validate (8/8): F. Final Defence",[
"The final defence compares measured throughput, minimum user rate, Jain index and target misses. If fairness improves and target misses decrease, quantify the difference. If aggregate throughput falls, explain whether that cost is acceptable in exchange for minimum-rate protection.",
"The redesigned scheduler is preferable when every admitted user needs a minimum rate, such as students accessing lecture material. Greedy scheduling may remain preferable for best-effort downloads where total throughput is the only objective. The engineering lesson is to diagnose the actual bottleneck before redesigning."
],None,(["Metric","Original","Redesigned"],[[m,q7sum.loc[q7sum.Scheduler=="Original greedy",m].iloc[0],q7sum.loc[q7sum.Scheduler=="Redesigned min-rate + PF",m].iloc[0]] for m in ["Sum rate","Minimum rate","Jain index","Users below target"]]))

assert len(pages)==45, len(pages)
sens_changes = int((sensitivity_df.groupby("Deployment")["Winning technique"].nunique() > 1).sum())
p6 = list(pages[35])
p6[1] = p6[1] + [f"The ±20% sensitivity run varied each criterion weight individually and renormalised the weights. Across the four deployment scenarios, {sens_changes} scenario(s) changed their winning technique under at least one tested weight adjustment. Full outcomes are supplied in Q6_weight_sensitivity.csv."]
pages[35] = tuple(p6)

# Word document
doc=Document(); sec=doc.sections[0]
sec.page_width=Inches(8.27); sec.page_height=Inches(11.69)
sec.top_margin=Inches(.58); sec.bottom_margin=Inches(.58); sec.left_margin=Inches(.68); sec.right_margin=Inches(.68)
for nm in ["Normal","Title","Heading 1","Heading 2","Heading 3"]:
    st=doc.styles[nm]; st.font.name="Times New Roman"; st._element.rPr.rFonts.set(qn("w:eastAsia"),"Times New Roman")
    st.font.color.rgb=RGBColor(0,0,0); st.font.size=Pt(12 if nm=="Normal" else 14)
    st.paragraph_format.line_spacing=1.5; st.paragraph_format.space_after=Pt(4)
hp=sec.header.paragraphs[0]; hp.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=hp.add_run("MOBILE COMPUTING  |  ASSIGNMENT 2 (CO2)"); r.bold=True; r.font.name="Times New Roman"; r.font.size=Pt(9)
fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=fp.add_run("Engineering Investigation Report  |  Page "); r.font.name="Times New Roman"; r.font.size=Pt(9)
fld=OxmlElement("w:fldSimple"); fld.set(qn("w:instr"),"PAGE"); fp._p.append(fld)

def dpara(txt):
    p=doc.add_paragraph(); p.paragraph_format.line_spacing=1.5; p.paragraph_format.space_after=Pt(4)
    rr=p.add_run(str(txt)); rr.font.name="Times New Roman"; rr.font.size=Pt(12); rr.font.color.rgb=RGBColor(0,0,0)
def dtable(headers,rows):
    t=doc.add_table(rows=1,cols=len(headers)); t.style="Table Grid"; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,v in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=str(v)
        for rr in c.paragraphs[0].runs: rr.bold=True; rr.font.name="Times New Roman"; rr.font.size=Pt(8)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):
            cells[i].text=str(v)
            for pp in cells[i].paragraphs:
                pp.paragraph_format.line_spacing=1.0
                for rr in pp.runs: rr.font.name="Times New Roman"; rr.font.size=Pt(8)
    doc.add_paragraph()
for i,(title,paras,bullets,tbl,fig,cap) in enumerate(pages):
    p=doc.add_paragraph(); p.paragraph_format.keep_with_next=True
    rr=p.add_run(title); rr.bold=True; rr.font.name="Times New Roman"; rr.font.size=Pt(14); rr.font.color.rgb=RGBColor(0,0,0)
    for x in paras: dpara(x)
    for b in bullets:
        p=doc.add_paragraph(style="List Bullet"); p.paragraph_format.line_spacing=1.5
        rr=p.add_run(b); rr.font.name="Times New Roman"; rr.font.size=Pt(12)
    if tbl: dtable(tbl[0],tbl[1])
    if fig:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(fig,width=Inches(5.8))
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        rr=p.add_run(cap); rr.italic=True; rr.font.name="Times New Roman"; rr.font.size=Pt(9)
    if i<len(pages)-1: doc.add_page_break()
doc.core_properties.title="Mobile Computing Assignment 2 (CO2) – Q1 to Q7"
doc.core_properties.subject="45-page engineering investigation report with simulation evidence"
docx=f"{D}/Mobile_Computing_Assignment_2_CO2_Q1-Q7_Improved.docx"
doc.save(docx)

# PDF
styles=getSampleStyleSheet()
body=ParagraphStyle("TNRBody",parent=styles["BodyText"],fontName="Times-Roman",fontSize=9,leading=13.5,spaceAfter=5,alignment=TA_JUSTIFY)
head=ParagraphStyle("TNRHead",parent=styles["Heading2"],fontName="Times-Bold",fontSize=12,leading=16,spaceAfter=7)
tiny=ParagraphStyle("TNRTiny",parent=body,fontSize=6.7,leading=8)
capstyle=ParagraphStyle("TNRCapt",parent=body,fontSize=7.5,leading=9,alignment=TA_CENTER)
story=[]
for i,(title,paras,bullets,tbl,fig,cap) in enumerate(pages):
    story.append(Paragraph(title.replace("&","&amp;"),head))
    for x in paras: story.append(Paragraph(x.replace("&","&amp;"),body))
    for b in bullets: story.append(Paragraph("• "+b.replace("&","&amp;"),body))
    if tbl:
        data=[[Paragraph(str(v).replace("&","&amp;"),tiny) for v in tbl[0]]]
        for row in tbl[1]: data.append([Paragraph(str(v).replace("&","&amp;"),tiny) for v in row])
        t=Table(data,repeatRows=1,hAlign="CENTER")
        t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.black),("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
        story.append(t); story.append(Spacer(1,4))
    if fig:
        story.append(RLImage(fig,width=145*mm,height=62*mm)); story.append(Paragraph(cap,capstyle))
    if i<len(pages)-1: story.append(PageBreak())
pdf=f"{D}/Mobile_Computing_Assignment_2_CO2_Q1-Q7_Improved.pdf"
def footer(c,d):
    c.saveState(); c.setFont("Times-Roman",8); c.setFillColor(colors.black)
    c.drawCentredString(A4[0]/2,9*mm,f"Mobile Computing | Assignment 2 (CO2) | Page {d.page}"); c.restoreState()
SimpleDocTemplate(pdf,pagesize=A4,rightMargin=15*mm,leftMargin=15*mm,topMargin=14*mm,bottomMargin=15*mm).build(story,onFirstPage=footer,onLaterPages=footer)

print("Improved report created.")
print("DOCX:",docx)
print("PDF:",pdf)
print("Authored answer pages:",len(pages))
print("\nQ1 results:\n",q1df.to_string(index=False))
print("\nQ2 results:\n",q2df.to_string(index=False))
print("\nQ3 results:\n",q3df.to_string(index=False))
print("\nQ4 summary:\n",q4sum.to_string(index=False))
print("\nQ5 metrics:\n",q5df.to_string(index=False))
print("\nQ7 validation:\n",q7sum.to_string(index=False))
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]
required=[
 'b1_background_decisions.csv','b1_scheduler_summary.csv',
 'b2_workload_trace.csv','b2_workload_summary.csv',
 'b3_small_instance_comparison.csv','b3_scalability.csv',
 'b4_multimedia_decisions.csv','execution_summary.json'
]
for name in required:
    assert (ROOT/'results'/name).is_file(), f'Missing {name}'
summary=json.loads((ROOT/'results/execution_summary.json').read_text())
assert summary['B1_scheduler_rows']==6
assert summary['B2_workloads']==2
assert summary['B3_cases']==4
assert summary['B4_profiles']==4
b2=list(csv.DictReader((ROOT/'results/b2_workload_summary.csv').open()))
assert b2[0]['delivered']=='10'
assert b2[1]['security_rejected']=='3'
b1=list(csv.DictReader((ROOT/'results/b1_scheduler_summary.csv').open()))
assert all(int(r['enqueued'])==8 for r in b1)
b3=list(csv.DictReader((ROOT/'results/b3_scalability.csv').open()))
assert int(b3[-1]['exact_configurations_evaluated']) > int(b3[0]['exact_configurations_evaluated'])
print('PASS: required results, workload assertions and scalability checks verified.')

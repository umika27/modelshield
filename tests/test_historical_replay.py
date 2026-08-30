"""Stage 4 deterministic historical replay coverage."""
from datetime import datetime, timezone
from dataclasses import replace
from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from integration import FailureMemoryAdapter, VerifiedFailureArtifact
from integration.service import AnalysisRequest, DatasetConfig, ModelConfig, ModelShieldService
from verification import FailureFingerprinter, VerificationResult

def req(candidate="future", challenge="clean"):
 return AnalysisRequest(ModelConfig("base","v1","resnet18"),ModelConfig(candidate,"v2","resnet18"),DatasetConfig("cifar10","/current"),challenge_type=challenge,verification_runs=1,experiment_id="exp")
def ev(r,eid):
 b=ModelMetadata("base:v1","base","v1","baseline"); c=ModelMetadata(f"{r.candidate.name}:v2",r.candidate.name,"v2","candidate")
 fail=(r.challenge_type in {"low_light","blur","reproduce"} and r.candidate.name not in {"fixed","current-fail"}) or (r.challenge_type=="clean" and r.candidate.name=="current-fail")
 score=.2 if r.candidate.name=="old" else (.1 if fail else .8)
 return EvaluationResult(eid,"exp",c,b,c,ChallengeSpec("c",r.challenge_type,{"level":1},seed=42),.9,score,-.15,"failure" if fail else "pass",42,datetime(2026,1,1,tzinfo=timezone.utc))
def store(memory, condition="low_light"):
 r=req("old",condition); x=ev(r,"old-eval"); fp=FailureFingerprinter().generate(x); v=VerificationResult(x.evaluation_id,x.experiment_id,True,1,1,(x,),"ok",fp); return memory.store(VerifiedFailureArtifact.from_verification(x,v))
def test_verified_failure_is_replayed_with_new_identity_and_scores(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); fid=store(m); out=ModelShieldService(memory=m,evaluator=ev).run_analysis(req("future"),replay_regressions=True)
 assert len(out.historical_replays)==1; replay=out.historical_replays[0]; assert replay.evaluation.candidate.name=="future"; assert replay.evaluation.candidate_score==.1; assert replay.evaluation.candidate_score != m.get_failure(fid)["candidate_score"]; assert out.release.verdict.value=="BLOCK"
def test_fixed_future_candidate_is_not_blacklisted(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m); out=ModelShieldService(memory=m,evaluator=ev).run_analysis(req("fixed")); assert out.historical_replays[0].outcome=="PASS"; assert out.release.verdict.value=="PASS"
def test_duplicate_and_invalid_history_are_safe(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m); m.ensure_model("x",role="candidate"); m.conn.execute("INSERT INTO failures (evaluation_id,fingerprint,condition,parameters,baseline_score,candidate_score,delta,severity,verified,model_id) VALUES (NULL,'sha256:'||replace(hex(randomblob(32)),'A','a'),'unsupported','{}',.9,.2,-.7,'critical',1,'x')"); m.conn.commit(); out=ModelShieldService(memory=m,evaluator=ev).run_analysis(req("fixed")); assert len(out.historical_replays)==2; assert any(x.outcome=="SKIPPED" for x in out.historical_replays); assert len(m.list_active_regressions())==2
def test_current_pass_replay_failure_blocks(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m); out=ModelShieldService(memory=m,evaluator=ev).run_analysis(req("future")); assert out.evaluation.status=="pass"; assert out.historical_replays[0].outcome=="FAIL"; assert out.release.verdict.value=="BLOCK"
def test_current_failure_replay_pass_does_not_erase_failure(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m); out=ModelShieldService(memory=m,evaluator=ev).run_analysis(req("current-fail")); assert out.evaluation.status=="failure"; assert out.historical_replays[0].outcome=="PASS"; assert out.release.verdict.value=="BLOCK"
def test_replay_disabled_and_no_history(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m); assert ModelShieldService(memory=m,evaluator=ev).run_analysis(req("fixed"),replay_regressions=False).historical_replays==(); assert ModelShieldService(memory=FailureMemoryAdapter(tmp_path/"empty.db"),evaluator=ev).run_analysis(req("fixed")).historical_replays==()
def test_multiple_replays_keep_pass_and_fail(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m,"low_light"); store(m,"blur"); out=ModelShieldService(memory=m,evaluator=lambda r,i: ev(r,i) if r.challenge_type!="blur" else ev(replace(r,challenge_type="clean"),i)).run_analysis(req("future")); assert len(out.historical_replays)==2; assert {x.outcome for x in out.historical_replays}=={"PASS","FAIL"}; assert all(x.evaluation.candidate.name=="future" for x in out.historical_replays); assert out.release.verdict.value=="BLOCK"
def test_duplicate_fingerprint_executes_once(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m); original=m.list_active_regressions(); m.list_active_regressions=lambda: original+original; out=ModelShieldService(memory=m,evaluator=ev).run_analysis(req("future")); assert len(out.historical_replays)==1
def test_active_regressions_are_verified_only(tmp_path):
 m=FailureMemoryAdapter(tmp_path/"m.db"); store(m); m.ensure_model("u",role="candidate"); m.conn.execute("INSERT INTO failures (fingerprint,condition,parameters,baseline_score,candidate_score,delta,severity,verified,model_id) VALUES ('sha256:'||replace(hex(randomblob(32)),'A','a'),'low_light','{}',.9,.2,-.7,'critical',0,'u')"); m.conn.commit(); assert len(m.list_active_regressions())==1

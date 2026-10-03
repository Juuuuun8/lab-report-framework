# データ項目の全仕様（v7.2）

現在の `schemas/*.json` から機械的に展開した一覧。過去の会話を根拠にしていない。必須は親オブジェクトが存在する場合の指定であり、処理段階に応じた追加必須条件は [システム仕様](SYSTEM_SPEC.md) を参照する。`$defs` は同じ表内の再利用定義。独自の補完・既定値の推測はしていない。

対象はJSONスキーマ19件。生成記録、本文受領バッチ、LAYOUT_TUNINGなど専用JSONスキーマを持たない形式はシステム仕様に記す。

## ACADEMIC_INTEGRITY.yaml

定義: [academic-integrity.schema.json](../schemas/academic-integrity.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["policy_status","ai_use","writing_authorship","disclosure","confirmations"]} |
| `policy_status` | 必須 | "制約から判定" | {"enum":["confirmed","not_provided"]} |
| `policy_source_locator` | 任意 | ["string","null"] | 追加制約なし |
| `ai_use` | 必須 | "object" | {"additionalProperties":false,"required":["status","allowed_uses","prohibited_uses","user_confirmed"]} |
| `ai_use.status` | 必須 | "制約から判定" | {"enum":["allowed","restricted","prohibited","unknown","not_applicable"]} |
| `ai_use.allowed_uses` | 必須 | "array" | 追加制約なし |
| `ai_use.allowed_uses[]` | 必須 | "string" | 追加制約なし |
| `ai_use.prohibited_uses` | 必須 | "array" | 追加制約なし |
| `ai_use.prohibited_uses[]` | 必須 | "string" | 追加制約なし |
| `ai_use.user_confirmed` | 必須 | "boolean" | 追加制約なし |
| `writing_authorship` | 必須 | "object" | {"additionalProperties":false,"required":["body_prose_owner","ai_may_generate_body","allowed_processing","meaning_change_requires_user_approval"]} |
| `writing_authorship.body_prose_owner` | 必須 | "制約から判定" | {"const":"user"} |
| `writing_authorship.ai_may_generate_body` | 必須 | "制約から判定" | {"const":false} |
| `writing_authorship.allowed_processing` | 必須 | "array" | {"minItems":1} |
| `writing_authorship.allowed_processing[]` | 必須 | "string" | {"minLength":1} |
| `writing_authorship.meaning_change_requires_user_approval` | 必須 | "制約から判定" | {"const":true} |
| `disclosure` | 必須 | "object" | {"additionalProperties":false,"required":["required","text"]} |
| `disclosure.required` | 必須 | ["boolean","null"] | 追加制約なし |
| `disclosure.text` | 必須 | ["string","null"] | 追加制約なし |
| `confirmations` | 必須 | "object" | {"additionalProperties":false,"required":["actual_work_status","data_not_fabricated","sources_not_fabricated","student_can_explain"]} |
| `confirmations.actual_work_status` | 必須 | "制約から判定" | {"enum":["confirmed","not_applicable","unconfirmed"]} |
| `confirmations.data_not_fabricated` | 必須 | "boolean" | 追加制約なし |
| `confirmations.sources_not_fabricated` | 必須 | "boolean" | 追加制約なし |
| `confirmations.student_can_explain` | 必須 | "boolean" | 追加制約なし |

## ASSIGNMENT_REQUIREMENTS.yaml

定義: [assignment-requirements.schema.json](../schemas/assignment-requirements.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["assignment","instruction_sources","requirements","rubric_source","rubric_criteria"]} |
| `task_scopes` | 任意 | "array" | {"minItems":1} |
| `task_scopes[]` | 必須 | "object" | {"additionalProperties":false,"required":["task_id","title","instruction_scope","prior_task_ids","allowed_knowledge","excluded_knowledge","requirement_ids","submission_code","helper_code","comment_policy"]} |
| `task_scopes[].task_id` | 必須 | "string" | {"pattern":"^TASK-[0-9]{3}$"} |
| `task_scopes[].title` | 必須 | "string" | {"minLength":1} |
| `task_scopes[].instruction_scope` | 必須 | "string" | {"minLength":1} |
| `task_scopes[].prior_task_ids` | 必須 | "array" | {"uniqueItems":true} |
| `task_scopes[].prior_task_ids[]` | 必須 | "string" | {"pattern":"^TASK-[0-9]{3}$"} |
| `task_scopes[].allowed_knowledge` | 必須 | "array" | {"minItems":1} |
| `task_scopes[].allowed_knowledge[]` | 必須 | "string" | {"minLength":1} |
| `task_scopes[].excluded_knowledge` | 必須 | "array" | 追加制約なし |
| `task_scopes[].excluded_knowledge[]` | 必須 | "string" | {"minLength":1} |
| `task_scopes[].requirement_ids` | 必須 | "array" | {"minItems":1,"uniqueItems":true} |
| `task_scopes[].requirement_ids[]` | 必須 | "string" | {"pattern":"^REQ-[0-9]{3}$"} |
| `task_scopes[].submission_code` | 必須 | "array" | {"uniqueItems":true} |
| `task_scopes[].submission_code[]` | 必須 | "string" | {"minLength":1} |
| `task_scopes[].helper_code` | 必須 | "array" | {"uniqueItems":true} |
| `task_scopes[].helper_code[]` | 必須 | "string" | {"minLength":1} |
| `task_scopes[].comment_policy` | 必須 | "string" | {"minLength":1} |
| `assignment` | 必須 | "object" | {"additionalProperties":false,"required":["course","title","submission_format","deadline"]} |
| `assignment.course` | 必須 | "string" | {"minLength":1} |
| `assignment.title` | 必須 | "string" | {"minLength":1} |
| `assignment.submission_format` | 必須 | "string" | {"minLength":1} |
| `assignment.deadline` | 必須 | ["string","null"] | 追加制約なし |
| `instruction_sources` | 必須 | "array" | {"minItems":1} |
| `instruction_sources[]` | 必須 | "object" | {"additionalProperties":false,"required":["instruction_id","path","read_complete","locator_scope"]} |
| `instruction_sources[].instruction_id` | 必須 | "string" | {"pattern":"^I-[0-9]{3}$"} |
| `instruction_sources[].path` | 必須 | "string" | {"minLength":1} |
| `instruction_sources[].sha256` | 任意 | ["string","null"] | {"pattern":"^[a-fA-F0-9]{64}$"} |
| `instruction_sources[].read_complete` | 必須 | "boolean" | 追加制約なし |
| `instruction_sources[].locator_scope` | 必須 | "string" | {"minLength":1} |
| `instruction_sources[].note` | 任意 | ["string","null"] | 追加制約なし |
| `requirements` | 必須 | "array" | {"minItems":1} |
| `requirements[]` | 必須 | "object" | {"additionalProperties":false,"required":["requirement_id","category","description","source_locator","mandatory","verification_method"]} |
| `requirements[].requirement_id` | 必須 | "string" | {"pattern":"^REQ-[0-9]{3}$"} |
| `requirements[].category` | 必須 | "制約から判定" | {"enum":["content","format","submission","experiment","prohibition"]} |
| `requirements[].description` | 必須 | "string" | {"minLength":1} |
| `requirements[].source_locator` | 必須 | "string" | {"minLength":1} |
| `requirements[].mandatory` | 必須 | "boolean" | 追加制約なし |
| `requirements[].verification_method` | 必須 | "string" | {"minLength":1} |
| `rubric_source` | 必須 | "object" | {"additionalProperties":false,"required":["status","confirmed_by_user","note"]} |
| `rubric_source.status` | 必須 | "制約から判定" | {"enum":["provided","not_provided_internal"]} |
| `rubric_source.confirmed_by_user` | 必須 | "boolean" | 追加制約なし |
| `rubric_source.note` | 必須 | "string" | {"minLength":1} |
| `rubric_criteria` | 必須 | "array" | {"minItems":1} |
| `rubric_criteria[]` | 必須 | "object" | {"additionalProperties":false,"required":["rubric_id","criterion","source_locator","required","acceptance_criteria"]} |
| `rubric_criteria[].rubric_id` | 必須 | "string" | {"pattern":"^RUB-[0-9]{3}$"} |
| `rubric_criteria[].criterion` | 必須 | "string" | {"minLength":1} |
| `rubric_criteria[].source_locator` | 必須 | "string" | {"minLength":1} |
| `rubric_criteria[].required` | 必須 | "boolean" | 追加制約なし |
| `rubric_criteria[].weight` | 任意 | ["number","null"] | {"minimum":0} |
| `rubric_criteria[].max_score` | 任意 | ["number","null"] | {"exclusiveMinimum":0} |
| `rubric_criteria[].acceptance_criteria` | 必須 | "array" | {"minItems":1} |
| `rubric_criteria[].acceptance_criteria[]` | 必須 | "string" | {"minLength":1} |

## CLAIMS.yaml

定義: [claims.schema.json](../schemas/claims.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["claims"]} |
| `claims` | 必須 | "array" | {"minItems":1} |
| `claims[]` | 必須 | "object" | {"additionalProperties":false,"required":["claim_id","kind","text","report_locator","source_ids","result_ids","status"]} |
| `claims[].claim_id` | 必須 | "string" | {"pattern":"^C-[0-9]{3}$"} |
| `claims[].kind` | 必須 | "制約から判定" | {"enum":["external","result","inference","limitation","method"]} |
| `claims[].text` | 必須 | "string" | {"minLength":1} |
| `claims[].report_locator` | 必須 | "string" | {"minLength":1} |
| `claims[].source_ids` | 必須 | "array" | 追加制約なし |
| `claims[].source_ids[]` | 必須 | "string" | {"pattern":"^S-[0-9]{3}$"} |
| `claims[].result_ids` | 必須 | "array" | 追加制約なし |
| `claims[].result_ids[]` | 必須 | "string" | {"pattern":"^R-[0-9]{3}$"} |
| `claims[].status` | 必須 | "制約から判定" | {"enum":["draft","verified","rejected"]} |
| `claims[].verification_note` | 任意 | "string" | 追加制約なし |

## CONTEXT_INDEX.yaml

定義: [context-index.schema.json](../schemas/context-index.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["documents"]} |
| `documents` | 必須 | "array" | {"minItems":1} |
| `documents[]` | 必須 | "object" | {"additionalProperties":false,"required":["path","sha256","verified_summary","related_gates","reread_when"]} |
| `documents[].path` | 必須 | "string" | {"minLength":1} |
| `documents[].sha256` | 必須 | ["string","null"] | {"pattern":"^[a-f0-9]{64}$"} |
| `documents[].verified_summary` | 必須 | "string" | {"minLength":1} |
| `documents[].related_gates` | 必須 | "array" | {"minItems":1} |
| `documents[].related_gates[]` | 必須 | "制約から判定" | {"enum":["G1","G2","G3"]} |
| `documents[].reread_when` | 必須 | "array" | {"minItems":1} |
| `documents[].reread_when[]` | 必須 | "string" | {"minLength":1} |

## EXECUTION_MANIFEST.yaml

定義: [execution-manifest.schema.json](../schemas/execution-manifest.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["environment","runs","sealed_at"]} |
| `environment` | 必須 | "object" | {"additionalProperties":false,"required":["recorded_at","hardware","operating_system","software"]} |
| `environment.recorded_at` | 必須 | "string" | {"minLength":10} |
| `environment.hardware` | 必須 | "string" | {"minLength":1} |
| `environment.operating_system` | 必須 | "string" | {"minLength":1} |
| `environment.software` | 必須 | "array" | {"minItems":1} |
| `environment.software[]` | 必須 | "string" | {"minLength":1} |
| `sealed_at` | 必須 | ["string","null"] | 追加制約なし |
| `runs` | 必須 | "array" | {"minItems":1} |
| `runs[]` | 必須 | "object" | {"additionalProperties":false,"required":["run_id","performed_at","condition","raw_files","status","deviation"]} |
| `runs[].run_id` | 必須 | "string" | {"pattern":"^RUN-[0-9]{3}$"} |
| `runs[].performed_at` | 必須 | "string" | {"minLength":10} |
| `runs[].condition` | 必須 | "string" | {"minLength":1} |
| `runs[].raw_files` | 必須 | "array" | {"minItems":1} |
| `runs[].raw_files[]` | 必須 | "object" | {"additionalProperties":false,"required":["path","sha256","bytes"]} |
| `runs[].raw_files[].path` | 必須 | "string" | {"minLength":1} |
| `runs[].raw_files[].sha256` | 必須 | ["string","null"] | {"pattern":"^[a-f0-9]{64}$"} |
| `runs[].raw_files[].bytes` | 必須 | ["integer","null"] | {"minimum":0} |
| `runs[].status` | 必須 | "制約から判定" | {"enum":["completed","failed","excluded","synthetic_example"]} |
| `runs[].deviation` | 必須 | ["string","null"] | 追加制約なし |

## EXPERIMENT_PLAN.yaml

定義: [experiment-plan.schema.json](../schemas/experiment-plan.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["status","objective","independent_variables","dependent_variables","controlled_variables","replications","execution_order","exclusion_rules","stop_conditions","analysis","safety_reviewed"]} |
| `status` | 必須 | "制約から判定" | {"enum":["draft","approved"]} |
| `objective` | 必須 | "string" | {"minLength":1} |
| `independent_variables` | 必須 | "array" | {"minItems":1} |
| `independent_variables[]` | 必須 | "string" | 追加制約なし |
| `dependent_variables` | 必須 | "array" | {"minItems":1} |
| `dependent_variables[]` | 必須 | "string" | 追加制約なし |
| `controlled_variables` | 必須 | "array" | 追加制約なし |
| `controlled_variables[]` | 必須 | "string" | 追加制約なし |
| `replications` | 必須 | "integer" | {"minimum":1} |
| `warmups` | 任意 | "integer" | {"minimum":0} |
| `random_seed` | 任意 | ["integer","null"] | 追加制約なし |
| `execution_order` | 必須 | "string" | {"minLength":1} |
| `exclusion_rules` | 必須 | "array" | {"minItems":1} |
| `exclusion_rules[]` | 必須 | "string" | 追加制約なし |
| `stop_conditions` | 必須 | "array" | {"minItems":1} |
| `stop_conditions[]` | 必須 | "string" | 追加制約なし |
| `analysis` | 必須 | "array" | {"minItems":1} |
| `analysis[]` | 必須 | "string" | 追加制約なし |
| `risks` | 任意 | "array" | 追加制約なし |
| `risks[]` | 必須 | "string" | 追加制約なし |
| `safety_reviewed` | 必須 | "boolean" | 追加制約なし |

## FINAL_CHECK.yaml

定義: [final-check.schema.json](../schemas/final-check.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["reviewed_pdf_sha256","reviewed_inputs_digest","visual_review","technical_review"]} |
| `reviewed_pdf_sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `reviewed_inputs_digest` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `visual_review` | 必須 | "制約から判定" | {"$ref":"#/$defs/review"} |
| `technical_review` | 必須 | "制約から判定" | {"$ref":"#/$defs/review"} |
| `$defs.review` | 任意 | "object" | {"additionalProperties":false,"required":["status","reviewer","reviewed_at","notes"]} |
| `$defs.review.status` | 必須 | "制約から判定" | {"enum":["passed","pending","failed"]} |
| `$defs.review.reviewer` | 必須 | "string" | {"minLength":1} |
| `$defs.review.reviewed_at` | 必須 | "string" | {"minLength":10} |
| `$defs.review.notes` | 必須 | "string" | {"minLength":1} |
| `$defs.review.rendered_pages` | 任意 | "integer" | {"minimum":0} |

## IMPROVEMENT_BACKLOG.yaml

定義: [improvement-backlog.schema.json](../schemas/improvement-backlog.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["items"]} |
| `items` | 必須 | "array" | 追加制約なし |
| `items[]` | 必須 | "object" | {"additionalProperties":false,"required":["improvement_id","level","problem","evidence","impact","proposal","status"]} |
| `items[].improvement_id` | 必須 | "string" | {"pattern":"^IMP-[0-9]{3}$"} |
| `items[].level` | 必須 | "制約から判定" | {"enum":["L0","L1","L2"]} |
| `items[].problem` | 必須 | "string" | {"minLength":1} |
| `items[].evidence` | 必須 | "array" | {"minItems":1} |
| `items[].evidence[]` | 必須 | "string" | {"minLength":1} |
| `items[].impact` | 必須 | "string" | {"minLength":1} |
| `items[].proposal` | 必須 | "string" | {"minLength":1} |
| `items[].status` | 必須 | "制約から判定" | {"enum":["candidate","approved","implemented","rejected"]} |
| `items[].user_decision` | 任意 | ["string","null"] | 追加制約なし |
| `items[].regression_test` | 任意 | ["string","null"] | 追加制約なし |
| `items[].token_effect` | 任意 | ["string","null"] | 追加制約なし |

## PROFESSOR_REVIEW.yaml

定義: [professor-review.schema.json](../schemas/professor-review.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["evaluator_role","reviewed_at","reviewed_pdf_sha256","reviewed_inputs_digest","rubric","overall","limitations"]} |
| `task_scope_reviews` | 任意 | "array" | {"minItems":1} |
| `task_scope_reviews[]` | 必須 | "object" | {"additionalProperties":false,"required":["task_id","status","evidence"]} |
| `task_scope_reviews[].task_id` | 必須 | "string" | {"pattern":"^TASK-[0-9]{3}$"} |
| `task_scope_reviews[].status` | 必須 | "制約から判定" | {"enum":["passed","failed","pending"]} |
| `task_scope_reviews[].evidence` | 必須 | "string" | {"minLength":1} |
| `evaluator_role` | 必須 | "制約から判定" | {"const":"codex_simulated_professor"} |
| `reviewed_at` | 必須 | "string" | {"minLength":10} |
| `reviewed_pdf_sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `reviewed_inputs_digest` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `rubric` | 必須 | "array" | {"minItems":1} |
| `rubric[]` | 必須 | "object" | {"additionalProperties":false,"required":["rubric_id","score","verdict","report_locators","evidence","criticism","improvement"]} |
| `rubric[].rubric_id` | 必須 | "string" | {"pattern":"^RUB-[0-9]{3}$"} |
| `rubric[].score` | 必須 | ["number","null"] | {"minimum":0} |
| `rubric[].verdict` | 必須 | "制約から判定" | {"enum":["met","partially_met","not_met","undetermined","not_applicable"]} |
| `rubric[].report_locators` | 必須 | "array" | {"minItems":1} |
| `rubric[].report_locators[]` | 必須 | "string" | {"minLength":1} |
| `rubric[].evidence` | 必須 | "array" | {"minItems":1} |
| `rubric[].evidence[]` | 必須 | "string" | {"minLength":1} |
| `rubric[].criticism` | 必須 | "string" | {"minLength":1} |
| `rubric[].improvement` | 必須 | "string" | {"minLength":1} |
| `overall` | 必須 | "object" | {"additionalProperties":false,"required":["score_percent","verdict","strengths","weaknesses"]} |
| `overall.score_percent` | 必須 | ["number","null"] | {"minimum":0,"maximum":100} |
| `overall.verdict` | 必須 | "制約から判定" | {"enum":["ready","revise"]} |
| `overall.strengths` | 必須 | "array" | {"minItems":1} |
| `overall.strengths[]` | 必須 | "string" | {"minLength":1} |
| `overall.weaknesses` | 必須 | "array" | {"minItems":1} |
| `overall.weaknesses[]` | 必須 | "string" | {"minLength":1} |
| `limitations` | 必須 | "string" | {"minLength":1} |

## QUALITY_REVIEW.yaml

定義: [quality-review.schema.json](../schemas/quality-review.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["reviewer","reviewed_at","reviewed_pdf_sha256","reviewed_inputs_digest","rubric","content_checks"]} |
| `reviewer` | 必須 | "string" | {"minLength":1} |
| `rubric_source` | 任意 | "制約から判定" | {"const":"professor_review"} |
| `reviewed_at` | 必須 | "string" | {"minLength":10} |
| `reviewed_pdf_sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `reviewed_inputs_digest` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `rubric` | 必須 | "array" | {"minItems":1} |
| `rubric[]` | 必須 | "object" | {"additionalProperties":false,"required":["rubric_id","status","report_locators","evidence","note"]} |
| `rubric[].rubric_id` | 必須 | "string" | {"pattern":"^RUB-[0-9]{3}$"} |
| `rubric[].status` | 必須 | "制約から判定" | {"enum":["passed","not_applicable","failed"]} |
| `rubric[].report_locators` | 必須 | "array" | 追加制約なし |
| `rubric[].report_locators[]` | 必須 | "string" | {"minLength":1} |
| `rubric[].evidence` | 必須 | "array" | 追加制約なし |
| `rubric[].evidence[]` | 必須 | "string" | {"minLength":1} |
| `rubric[].note` | 必須 | "string" | {"minLength":1} |
| `content_checks` | 必須 | "object" | {"additionalProperties":false,"required":["requirements_coverage","technical_accuracy","quantitative_consistency","argument_quality","limitations","source_quality","academic_integrity","oral_defense"]} |
| `content_checks.requirements_coverage` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `content_checks.technical_accuracy` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `content_checks.quantitative_consistency` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `content_checks.argument_quality` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `content_checks.limitations` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `content_checks.source_quality` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `content_checks.academic_integrity` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `content_checks.oral_defense` | 必須 | "制約から判定" | {"$ref":"#/$defs/check"} |
| `$defs.check` | 任意 | "object" | {"additionalProperties":false,"required":["status","evidence"]} |
| `$defs.check.status` | 必須 | "制約から判定" | {"enum":["passed","failed"]} |
| `$defs.check.evidence` | 必須 | "string" | {"minLength":1} |

## RENDER_MANIFEST.yaml

定義: [render-manifest.schema.json](../schemas/render-manifest.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["source_sha256","rendered_at","dpi","page_count","pages"]} |
| `source_sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `rendered_at` | 必須 | "string" | 追加制約なし |
| `dpi` | 必須 | "integer" | {"minimum":120} |
| `page_count` | 必須 | "integer" | {"minimum":1} |
| `pages` | 必須 | "array" | {"minItems":1} |
| `pages[]` | 必須 | "object" | {"additionalProperties":false,"required":["path","sha256","bytes"]} |
| `pages[].path` | 必須 | "string" | {"minLength":1} |
| `pages[].sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `pages[].bytes` | 必須 | "integer" | {"minimum":1} |

## REPORT_META.yaml

定義: [report-meta.schema.json](../schemas/report-meta.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"$id":"https://example.invalid/lab-report/report-meta.schema.json","additionalProperties":false,"required":["cover","document"]} |
| `cover` | 必須 | "object" | {"additionalProperties":false,"required":["course_name","title","fields"]} |
| `cover.course_name` | 必須 | "string" | {"minLength":1} |
| `cover.title` | 必須 | "string" | {"minLength":1} |
| `cover.subtitle` | 任意 | "string" | 追加制約なし |
| `cover.fields` | 必須 | "array" | {"minItems":1} |
| `cover.fields[]` | 必須 | "object" | {"additionalProperties":false,"required":["label","value"]} |
| `cover.fields[].label` | 必須 | "string" | {"minLength":1} |
| `cover.fields[].value` | 必須 | "string" | {"minLength":1} |
| `document` | 必須 | "object" | {"additionalProperties":false,"required":["language","paper","columns","body_font_pt"]} |
| `document.language` | 必須 | "制約から判定" | {"const":"ja"} |
| `document.paper` | 必須 | "制約から判定" | {"const":"A4"} |
| `document.columns` | 必須 | "制約から判定" | {"const":1} |
| `document.body_font_pt` | 必須 | "制約から判定" | {"const":10.5} |
| `document.punctuation` | 任意 | "制約から判定" | {"enum":["，．","、。"]} |

## REPRODUCE.yaml

定義: [reproduce.schema.json](../schemas/reproduce.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["commands","expected_outputs","sealed_at"]} |
| `commands` | 必須 | "array" | {"minItems":1} |
| `commands[]` | 必須 | "object" | {"additionalProperties":false,"required":["command_id","argv","cwd"]} |
| `commands[].command_id` | 必須 | "string" | {"pattern":"^A-[0-9]{3}$"} |
| `commands[].argv` | 必須 | "array" | {"minItems":1} |
| `commands[].argv[]` | 必須 | "string" | {"minLength":1} |
| `commands[].cwd` | 必須 | "string" | {"minLength":1} |
| `expected_outputs` | 必須 | "array" | {"minItems":1} |
| `expected_outputs[]` | 必須 | "object" | {"additionalProperties":false,"required":["path","sha256","bytes"]} |
| `expected_outputs[].path` | 必須 | "string" | {"minLength":1} |
| `expected_outputs[].sha256` | 必須 | ["string","null"] | {"pattern":"^[a-f0-9]{64}$"} |
| `expected_outputs[].bytes` | 必須 | ["integer","null"] | {"minimum":0} |
| `sealed_at` | 必須 | ["string","null"] | 追加制約なし |

## SOURCES.yaml

定義: [sources.schema.json](../schemas/sources.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["sources"]} |
| `sources` | 必須 | "array" | 追加制約なし |
| `sources[]` | 必須 | "object" | {"additionalProperties":false,"required":["source_id","language","source_class","organization","title","url","accessed_at","verification"]} |
| `sources[].source_id` | 必須 | "string" | {"pattern":"^S-[0-9]{3}$"} |
| `sources[].language` | 必須 | "制約から判定" | {"enum":["ja","en"]} |
| `sources[].source_class` | 必須 | "制約から判定" | {"enum":["primary_official","primary_research","secondary_reliable"]} |
| `sources[].organization` | 必須 | "string" | {"minLength":1} |
| `sources[].title` | 必須 | "string" | {"minLength":1} |
| `sources[].url` | 必須 | "string" | {"format":"uri"} |
| `sources[].published_or_updated_at` | 任意 | ["string","null"] | 追加制約なし |
| `sources[].accessed_at` | 必須 | "string" | {"minLength":10} |
| `sources[].verification` | 必須 | "object" | {"additionalProperties":false,"required":["status","locator","supports_claims","match_note","selection_note"]} |
| `sources[].verification.status` | 必須 | "制約から判定" | {"enum":["candidate","verified","rejected"]} |
| `sources[].verification.locator` | 必須 | "string" | 追加制約なし |
| `sources[].verification.supports_claims` | 必須 | "array" | 追加制約なし |
| `sources[].verification.supports_claims[]` | 必須 | "string" | {"pattern":"^C-[0-9]{3}$"} |
| `sources[].verification.match_note` | 必須 | "string" | 追加制約なし |
| `sources[].verification.selection_note` | 必須 | "string" | 追加制約なし |

## config/style-contract.yaml

定義: [style-contract.schema.json](../schemas/style-contract.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["revision","class_path","normalized_sha256","invariants","change_control"]} |
| `revision` | 必須 | "integer" | {"minimum":1} |
| `class_path` | 必須 | "制約から判定" | {"const":"tex/labreport.cls"} |
| `normalized_sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `invariants` | 必須 | "object" | {"additionalProperties":false,"required":["paper","columns","body_font_pt","margins_mm","figure_caption","table_caption","listing_caption","cover_fields_alignment","floats_cross_section","multiline_caption"]} |
| `invariants.paper` | 必須 | "制約から判定" | {"const":"A4"} |
| `invariants.columns` | 必須 | "制約から判定" | {"const":1} |
| `invariants.body_font_pt` | 必須 | "制約から判定" | {"const":10.5} |
| `invariants.margins_mm` | 必須 | "制約から判定" | {"const":25} |
| `invariants.figure_caption` | 必須 | "制約から判定" | {"const":"bottom"} |
| `invariants.table_caption` | 必須 | "制約から判定" | {"const":"top"} |
| `invariants.listing_caption` | 必須 | "制約から判定" | {"const":"top"} |
| `invariants.cover_fields_alignment` | 必須 | "制約から判定" | {"const":"centered_block"} |
| `invariants.floats_cross_section` | 必須 | "制約から判定" | {"const":false} |
| `invariants.multiline_caption` | 必須 | "制約から判定" | {"const":"justified"} |
| `change_control` | 必須 | "string" | {"minLength":1} |

## STYLE_OVERRIDES.yaml

定義: [style-overrides.schema.json](../schemas/style-overrides.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["overrides"]} |
| `overrides` | 必須 | "array" | 追加制約なし |
| `overrides[]` | 必須 | "object" | {"additionalProperties":false,"required":["override_id","setting","value","reason","source_locator","approved_by","approved_at"]} |
| `overrides[].override_id` | 必須 | "string" | {"pattern":"^OVR-[0-9]{3}$"} |
| `overrides[].setting` | 必須 | "string" | {"minLength":1} |
| `overrides[].value` | 必須 | "制約から判定" | 追加制約なし |
| `overrides[].reason` | 必須 | "string" | {"minLength":1} |
| `overrides[].source_locator` | 必須 | "string" | {"minLength":1} |
| `overrides[].approved_by` | 必須 | "制約から判定" | {"enum":["user","instructor"]} |
| `overrides[].approved_at` | 必須 | "string" | {"minLength":10} |

## USER_DECISIONS.yaml

定義: [user-decisions.schema.json](../schemas/user-decisions.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["instructions_read_complete","instructions_read_at","questions"]} |
| `instructions_read_complete` | 必須 | "boolean" | 追加制約なし |
| `instructions_read_at` | 必須 | ["string","null"] | 追加制約なし |
| `questions` | 必須 | "array" | 追加制約なし |
| `questions[]` | 必須 | "object" | {"additionalProperties":false,"required":["id","required_before_experiment","status","question","decision","decided_by","decided_at"]} |
| `questions[].id` | 必須 | "string" | {"pattern":"^Q-[0-9]{3}$"} |
| `questions[].required_before_experiment` | 必須 | "boolean" | 追加制約なし |
| `questions[].status` | 必須 | "制約から判定" | {"enum":["open","resolved","delegated"]} |
| `questions[].question` | 必須 | "string" | {"minLength":1} |
| `questions[].decision` | 必須 | ["string","null"] | 追加制約なし |
| `questions[].decided_by` | 必須 | "制約から判定" | {"enum":["user","codex",null]} |
| `questions[].decided_at` | 必須 | ["string","null"] | 追加制約なし |
| `questions[].rationale` | 任意 | ["string","null"] | 追加制約なし |

## workflow/STATE.yaml

定義: [workflow-state.schema.json](../schemas/workflow-state.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["version","current_gate","status","example_only","gates"]} |
| `version` | 必須 | "制約から判定" | {"enum":[1,2]} |
| `current_gate` | 必須 | "制約から判定" | {"enum":["G1","G2","G3","complete"]} |
| `status` | 必須 | "制約から判定" | {"enum":["preparing","awaiting_user","executing","approved","released"]} |
| `example_only` | 必須 | "boolean" | 追加制約なし |
| `released_at` | 任意 | "string" | 追加制約なし |
| `release_sha256` | 任意 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `gates` | 必須 | "object" | {"additionalProperties":false,"required":["G1","G2","G3"]} |
| `gates.G1` | 必須 | "制約から判定" | {"$ref":"#/$defs/gate"} |
| `gates.G2` | 必須 | "制約から判定" | {"$ref":"#/$defs/gate"} |
| `gates.G3` | 必須 | "制約から判定" | {"$ref":"#/$defs/gate"} |
| `$defs.gate` | 任意 | "object" | {"additionalProperties":false,"required":["status","prepared_at","decided_at","decided_by","decision_text","artifact_digest","artifact_count","review_file"]} |
| `$defs.gate.status` | 必須 | "制約から判定" | {"enum":["pending","awaiting_user","approved"]} |
| `$defs.gate.prepared_at` | 必須 | ["string","null"] | 追加制約なし |
| `$defs.gate.decided_at` | 必須 | ["string","null"] | 追加制約なし |
| `$defs.gate.decided_by` | 必須 | "制約から判定" | {"enum":["user","framework_migration",null]} |
| `$defs.gate.decision_text` | 必須 | ["string","null"] | 追加制約なし |
| `$defs.gate.artifact_digest` | 必須 | ["string","null"] | {"pattern":"^[a-f0-9]{64}$"} |
| `$defs.gate.artifact_count` | 必須 | "integer" | {"minimum":0} |
| `$defs.gate.review_file` | 必須 | "string" | 追加制約なし |
| `$defs.gate.artifacts` | 任意 | "array" | 追加制約なし |
| `$defs.gate.artifacts[]` | 必須 | "object" | {"additionalProperties":false,"required":["path","sha256","bytes"]} |
| `$defs.gate.artifacts[].path` | 必須 | "string" | 追加制約なし |
| `$defs.gate.artifacts[].sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `$defs.gate.artifacts[].bytes` | 必須 | "integer" | {"minimum":0} |

## WRITING_PLAN.yaml

定義: [writing-plan.schema.json](../schemas/writing-plan.schema.json)

| 項目 | 必須 | 型 | 制約 |
|---|---|---|---|
| `$` | 必須 | "object" | {"additionalProperties":false,"required":["version","status","skeleton_pdf","slots"]} |
| `task_scope_reviews` | 任意 | "array" | {"minItems":1} |
| `task_scope_reviews[]` | 必須 | "object" | {"additionalProperties":false,"required":["task_id","status","evidence"]} |
| `task_scope_reviews[].task_id` | 必須 | "string" | {"pattern":"^TASK-[0-9]{3}$"} |
| `task_scope_reviews[].status` | 必須 | "制約から判定" | {"enum":["passed","failed","pending"]} |
| `task_scope_reviews[].evidence` | 必須 | "string" | {"minLength":1} |
| `version` | 必須 | "制約から判定" | {"const":1} |
| `status` | 必須 | "制約から判定" | {"enum":["planning","skeleton_ready","prose_partial","prose_complete"]} |
| `skeleton_pdf` | 必須 | "制約から判定" | {"const":"build/skeleton.pdf"} |
| `slots` | 必須 | "array" | {"minItems":1} |
| `slots[]` | 必須 | "object" | {"additionalProperties":false,"required":["slot_id","display_label","section","purpose","required_points","planned_references","evidence_ids","rubric_ids","authorship","status","original_file","original_sha256","typeset_file","semantic_change","proofread_notes"]} |
| `slots[].task_ids` | 任意 | "array" | {"minItems":1,"uniqueItems":true} |
| `slots[].task_ids[]` | 必須 | "string" | {"pattern":"^TASK-[0-9]{3}$"} |
| `slots[].slot_id` | 必須 | "string" | {"pattern":"^P-[0-9]{3}$"} |
| `slots[].display_label` | 必須 | "string" | {"pattern":"^文章[0-9]+$"} |
| `slots[].section` | 必須 | "string" | {"minLength":1} |
| `slots[].purpose` | 必須 | "string" | {"minLength":1} |
| `slots[].student_judgment` | 任意 | "string" | {"minLength":1} |
| `slots[].required_points` | 必須 | "array" | {"minItems":1} |
| `slots[].required_points[]` | 必須 | "string" | {"minLength":1} |
| `slots[].planned_references` | 必須 | "array" | 追加制約なし |
| `slots[].planned_references[]` | 必須 | "string" | {"pattern":"^[A-Za-z0-9:_-]+$"} |
| `slots[].evidence_ids` | 必須 | "array" | 追加制約なし |
| `slots[].evidence_ids[]` | 必須 | "string" | {"minLength":1} |
| `slots[].rubric_ids` | 必須 | "array" | {"minItems":1} |
| `slots[].rubric_ids[]` | 必須 | "string" | {"pattern":"^RUB-[0-9]{3}$"} |
| `slots[].authorship` | 必須 | "制約から判定" | {"enum":["user","example_fixture"]} |
| `slots[].status` | 必須 | "制約から判定" | {"enum":["awaiting_user","user_submitted","typeset"]} |
| `slots[].original_file` | 必須 | "string" | {"pattern":"^prose/original/P-[0-9]{3}\\.md$"} |
| `slots[].original_sha256` | 必須 | ["string","null"] | {"pattern":"^[a-f0-9]{64}$"} |
| `slots[].typeset_file` | 必須 | "string" | {"pattern":"^prose/typeset/P-[0-9]{3}\\.tex$"} |
| `slots[].semantic_change` | 必須 | "制約から判定" | {"enum":["none","user_approved","pending_user_approval"]} |
| `slots[].proofread_notes` | 必須 | ["string","null"] | 追加制約なし |
| `slots[].review` | 任意 | "object" | {"additionalProperties":false,"required":["original_sha256","typeset_sha256","status","decision_text","note","reviewed_at"]} |
| `slots[].review.original_sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `slots[].review.typeset_sha256` | 必須 | "string" | {"pattern":"^[a-f0-9]{64}$"} |
| `slots[].review.status` | 必須 | "制約から判定" | {"enum":["meaning_unchanged","user_approved"]} |
| `slots[].review.decision_text` | 必須 | ["string","null"] | 追加制約なし |
| `slots[].review.note` | 必須 | "string" | {"minLength":1} |
| `slots[].review.reviewed_at` | 必須 | "string" | {"minLength":10} |

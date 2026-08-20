#!/usr/bin/env python3
"""
AI Incident Investigator - Synthetic Data Generator
Implements AI_Incident_Investigator_Data_Generation_Spec.md

Produces:
  - agents.csv, policies.csv, actions.csv, investigations.csv
  - seed.sql (INSERT statements for all four tables)

Deterministic: fixed SEED = 42
"""

import random
import csv
import os
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output_data")
os.makedirs(OUT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# 1. AGENTS
# ------------------------------------------------------------------
AGENTS = [
    ("A001", "RefundBot", "Refund processing", 0.18),
    ("A002", "OrderBot", "Order management", 0.16),
    ("A003", "DeliveryBot", "Delivery/logistics", 0.13),
    ("A004", "PaymentBot", "Payment processing", 0.10),
    ("A005", "SupportBot", "Customer support", 0.10),
    ("A006", "ReturnBot", "Returns", 0.09),
    ("A007", "AccountBot", "Account management", 0.08),
    ("A008", "DiscountBot", "Sales/discounts", 0.06),
    ("A009", "ClaimsBot", "Claims handling", 0.06),
    ("A010", "NotificationBot", "Customer notifications", 0.04),
]
AGENT_IDS = [a[0] for a in AGENTS]
AGENT_WEIGHTS = {a[0]: a[3] for a in AGENTS}
BASE_DATE = datetime(2026, 5, 1, 8, 0, 0)

def weighted_agent(pool=None):
    pool = pool or AGENT_IDS
    weights = [AGENT_WEIGHTS[a] for a in pool]
    return random.choices(pool, weights=weights, k=1)[0]

# ------------------------------------------------------------------
# 2. POLICIES
# ------------------------------------------------------------------
POLICIES = [
    ("P001", "High Value Refund", "Refund amount > 5000", "ESCALATE", "HIGH"),
    ("P002", "Undelivered Order Refund", "Order not delivered", "BLOCK", "HIGH"),
    ("P003", "Duplicate Refund", "Order already refunded", "BLOCK", "HIGH"),
    ("P004", "Missing Order", "Order cannot be found", "BLOCK", "HIGH"),
    ("P005", "Unauthorized Refund Agent", "Agent not permitted to refund", "BLOCK", "HIGH"),
    ("P006", "High Value Payment", "Payment amount > 10000", "ESCALATE", "HIGH"),
    ("P007", "Cancelled Order Action", "Order is cancelled", "BLOCK", "MEDIUM"),
    ("P008", "Missing Required Information", "Required information unavailable", "BLOCK", "MEDIUM"),
]

# ------------------------------------------------------------------
# Global counters / registries
# ------------------------------------------------------------------
action_counter = 1
incident_counter = 1
investigation_counter = 1

actions_rows = []       # list of dicts
investigations_rows = []

order_counter = 1000
customer_counter = 5000

def next_action_id():
    global action_counter
    aid = f"ACT{action_counter:06d}"
    action_counter += 1
    return aid

def next_incident_id():
    global incident_counter
    iid = f"INC{incident_counter:04d}"
    incident_counter += 1
    return iid

def next_investigation_id():
    global investigation_counter
    vid = f"INV{investigation_counter:04d}"
    investigation_counter += 1
    return vid

def next_order_id():
    global order_counter
    order_counter += 1
    return f"ORD{order_counter:05d}"

def next_customer_id():
    global customer_counter
    customer_counter += 1
    return f"CUST{customer_counter:05d}"

def random_ts(day_offset_range=(0, 75)):
    """Random base timestamp spread across ~11 weeks, business hours weighted."""
    day = random.randint(*day_offset_range)
    hour = random.choices(
        population=list(range(7, 22)),
        weights=[2,3,5,7,8,9,9,8,7,8,9,8,6,4,2],
        k=1
    )[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return BASE_DATE + timedelta(days=day, hours=hour - 8, minutes=minute, seconds=second)

def step_forward(ts, min_s=5, max_s=240):
    return ts + timedelta(seconds=random.randint(min_s, max_s))

def add_action(agent_id, action_type, ts, outcome="SUCCESS", order_id=None,
               customer_id=None, reference_id=None, policy_id=None,
               incident_id=None, details=""):
    row = {
        "action_id": next_action_id(),
        "agent_id": agent_id,
        "action_type": action_type,
        "order_id": order_id or "",
        "customer_id": customer_id or "",
        "reference_id": reference_id or "",
        "action_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "outcome": outcome,
        "policy_id": policy_id or "",
        "incident_id": incident_id or "",
        "details": details,
    }
    actions_rows.append(row)
    return row

# ------------------------------------------------------------------
# 5. NORMAL ACTION WORKFLOWS (~750 rows)
# ------------------------------------------------------------------
NORMAL_WORKFLOWS = [
    # (agent pool, action sequence)
    (["A001", "A009"], ["GET_ORDER", "CHECK_DELIVERY", "CHECK_ELIGIBILITY", "CALCULATE_REFUND", "REFUND"]),
    (["A002", "A007"], ["GET_ORDER", "UPDATE_RECORD", "SEND_MESSAGE"]),
    (["A003"],         ["GET_ORDER", "CHECK_DELIVERY", "SHIP", "SEND_MESSAGE"]),
    (["A004"],         ["GET_ORDER", "CHECK_ELIGIBILITY", "PAYMENT"]),
    (["A006"],         ["GET_ORDER", "CHECK_DELIVERY", "RETURN", "UPDATE_RECORD"]),
    (["A008"],         ["GET_ORDER", "APPLY_DISCOUNT", "SEND_MESSAGE"]),
    (["A002"],         ["GET_ORDER", "CHECK_ELIGIBILITY", "CANCEL_ORDER", "SEND_MESSAGE"]),
    (["A010", "A005"], ["GET_ORDER", "SEND_MESSAGE"]),
    (["A005"],         ["GET_ORDER", "CHECK_ELIGIBILITY", "UPDATE_RECORD", "SEND_MESSAGE"]),
]

def generate_normal_actions(target=750):
    generated = 0
    while generated < target:
        pool, seq = random.choice(NORMAL_WORKFLOWS)
        agent = weighted_agent(pool)
        order_id = next_order_id()
        customer_id = next_customer_id()
        ts = random_ts()
        for i, atype in enumerate(seq):
            if generated >= target:
                break
            outcome = "SUCCESS" if random.random() > 0.04 else "FAILED"
            details = ""
            if atype == "REFUND":
                amt = round(random.uniform(15, 900), 2)
                details = f"refund_amount={amt}"
            elif atype == "PAYMENT":
                amt = round(random.uniform(20, 3000), 2)
                details = f"payment_amount={amt}"
            add_action(agent, atype, ts, outcome=outcome, order_id=order_id,
                       customer_id=customer_id, details=details)
            ts = step_forward(ts)
            generated += 1
    return generated

# ------------------------------------------------------------------
# 6/7. INCIDENT SCENARIOS (~250 actions across ~40 incidents)
# ------------------------------------------------------------------

def scenario_stale_data(n):
    """GET_ORDER -> (time passes) -> agent uses stale data -> business action, without re-checking."""
    agents = ["A001", "A006", "A009", "A002"]
    for _ in range(n):
        agent = weighted_agent(agents)
        order_id = next_order_id()
        customer_id = next_customer_id()
        incident_id = next_incident_id()
        ts = random_ts()
        evidence = []
        r = add_action(agent, "GET_ORDER", ts, order_id=order_id, customer_id=customer_id,
                        details="order_snapshot_captured=true", incident_id=incident_id)
        evidence.append(r["action_id"])
        # a large stale gap before continuing (data goes stale, no refresh)
        ts = ts + timedelta(hours=random.randint(6, 48))
        r = add_action(agent, "CHECK_DELIVERY", ts, order_id=order_id, customer_id=customer_id,
                        details="using_cached_snapshot=true;snapshot_age_hours=" + str(random.randint(6,48)),
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts)
        atype, outcome = random.choice([("REFUND", "SUCCESS"), ("SHIP", "SUCCESS"), ("UPDATE_RECORD", "SUCCESS")])
        details = "action_based_on_stale_data=true;no_refresh_before_action=true"
        r = add_action(agent, atype, ts, order_id=order_id, customer_id=customer_id,
                        outcome=outcome, details=details, incident_id=incident_id)
        evidence.append(r["action_id"])
        make_investigation(incident_id, "STALE_DATA", "MEDIUM", evidence,
            f"{agent} acted on an order snapshot for {order_id} that was "
            f"{ts.strftime('%H:%M')} stale without refreshing delivery/eligibility data before {atype}.")

def scenario_missing_information(n):
    agents = ["A001", "A006", "A005", "A009"]
    for _ in range(n):
        agent = weighted_agent(agents)
        order_id = next_order_id()
        customer_id = next_customer_id()
        incident_id = next_incident_id()
        ts = random_ts()
        evidence = []
        r = add_action(agent, "GET_ORDER", ts, order_id=order_id, customer_id=customer_id,
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts)
        r = add_action(agent, "CHECK_DELIVERY", ts, order_id=order_id, customer_id=customer_id,
                        outcome="FAILED", details="delivery_status=UNAVAILABLE", incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts)
        atype = random.choice(["REFUND", "RETURN", "CANCEL_ORDER"])
        r = add_action(agent, atype, ts, order_id=order_id, customer_id=customer_id,
                        outcome="SUCCESS", details="proceeded_despite_missing_delivery_status=true",
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        make_investigation(incident_id, "MISSING_INFORMATION", "HIGH", evidence,
            f"{agent} proceeded to {atype} on {order_id} even though delivery status "
            f"was unavailable, skipping a required data dependency.")

def scenario_incorrect_sequence(n):
    agents = ["A001", "A006", "A002", "A009"]
    for _ in range(n):
        agent = weighted_agent(agents)
        order_id = next_order_id()
        customer_id = next_customer_id()
        incident_id = next_incident_id()
        ts = random_ts()
        evidence = []
        r = add_action(agent, "GET_ORDER", ts, order_id=order_id, customer_id=customer_id,
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts)
        r = add_action(agent, "CHECK_ELIGIBILITY", ts, order_id=order_id, customer_id=customer_id,
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts)
        amt = round(random.uniform(20, 1500), 2)
        # CHECK_DELIVERY / CALCULATE_REFUND step skipped entirely
        r = add_action(agent, "REFUND", ts, order_id=order_id, customer_id=customer_id,
                        outcome="SUCCESS", details=f"refund_amount={amt};delivery_verification_skipped=true",
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        make_investigation(incident_id, "INCORRECT_SEQUENCE", "HIGH", evidence,
            f"{agent} issued a refund on {order_id} without a preceding CHECK_DELIVERY / "
            f"CALCULATE_REFUND step, violating the standard verification sequence.")

def scenario_duplicate_action(n):
    agents = ["A001", "A004", "A009"]
    for _ in range(n):
        agent = weighted_agent(agents)
        order_id = next_order_id()
        customer_id = next_customer_id()
        incident_id = next_incident_id()
        ts = random_ts()
        evidence = []
        r = add_action(agent, "GET_ORDER", ts, order_id=order_id, customer_id=customer_id,
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts)
        atype = random.choice(["REFUND", "PAYMENT"])
        amt = round(random.uniform(20, 2000), 2)
        r = add_action(agent, atype, ts, order_id=order_id, customer_id=customer_id,
                        outcome="SUCCESS", details=f"{atype.lower()}_amount={amt};txn_ref=TXN{random.randint(10000,99999)}",
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts, min_s=30, max_s=600)
        r = add_action(agent, atype, ts, order_id=order_id, customer_id=customer_id,
                        outcome="SUCCESS", details=f"{atype.lower()}_amount={amt};duplicate_of_prior_transaction=true",
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        make_investigation(incident_id, "DUPLICATE_ACTION", "HIGH", evidence,
            f"{agent} executed {atype} twice for order {order_id} referencing the same "
            f"amount ({amt}), indicating a duplicate business action was not caught.")

def scenario_policy_gap(n):
    """Problematic but not covered by any of the 8 defined policies."""
    agents = ["A008", "A007", "A010", "A003"]
    gap_templates = [
        ("APPLY_DISCOUNT", "discount_pct=90;no_max_discount_policy_defined=true",
         "applied an unusually large discount with no policy limiting maximum discount percentage"),
        ("UPDATE_RECORD", "field=customer_email;changed_without_verification=true",
         "changed customer contact information without any identity-verification policy in place"),
        ("SEND_MESSAGE", "message_count_last_hour=27;no_rate_limit_policy=true",
         "sent an unusually high volume of messages to the same customer with no messaging rate-limit policy"),
        ("CANCEL_ORDER", "order_age_minutes=2;no_cooldown_policy=true",
         "cancelled an order within minutes of placement with no minimum-cooldown policy defined"),
    ]
    for _ in range(n):
        agent = weighted_agent(agents)
        order_id = next_order_id()
        customer_id = next_customer_id()
        incident_id = next_incident_id()
        ts = random_ts()
        evidence = []
        r = add_action(agent, "GET_ORDER", ts, order_id=order_id, customer_id=customer_id,
                        incident_id=incident_id)
        evidence.append(r["action_id"])
        ts = step_forward(ts)
        atype, details, narrative = random.choice(gap_templates)
        r = add_action(agent, atype, ts, order_id=order_id, customer_id=customer_id,
                        outcome="SUCCESS", details=details, incident_id=incident_id)
        evidence.append(r["action_id"])
        make_investigation(incident_id, "POLICY_GAP", "MEDIUM", evidence,
            f"{agent} {narrative} on {order_id}. No existing policy (P001-P008) covers this "
            f"behavior, indicating a gap in the current rule set.")

def scenario_wrong_input_tool_failure(n):
    agents = ["A002", "A001", "A003", "A004"]
    for _ in range(n):
        agent = weighted_agent(agents)
        wrong_order_id = next_order_id()
        real_order_id = next_order_id()
        customer_id = next_customer_id()
        incident_id = next_incident_id()
        ts = random_ts()
        evidence = []
        cause = random.choice(["WRONG_INPUT", "TOOL_FAILURE"])
        if cause == "WRONG_INPUT":
            r = add_action(agent, "GET_ORDER", ts, order_id=wrong_order_id, customer_id=customer_id,
                            outcome="FAILED", details=f"requested_order={wrong_order_id};intended_order={real_order_id};lookup_mismatch=true",
                            incident_id=incident_id)
            evidence.append(r["action_id"])
            ts = step_forward(ts)
            atype = random.choice(["REFUND", "UPDATE_RECORD", "CANCEL_ORDER"])
            r = add_action(agent, atype, ts, order_id=wrong_order_id, customer_id=customer_id,
                            outcome="FAILED", details="acted_on_incorrect_order_id=true",
                            incident_id=incident_id)
            evidence.append(r["action_id"])
            narrative = (f"{agent} looked up order {wrong_order_id} instead of the intended "
                         f"{real_order_id} and proceeded to {atype} against the wrong order.")
        else:
            r = add_action(agent, "GET_ORDER", ts, order_id=real_order_id, customer_id=customer_id,
                            incident_id=incident_id)
            evidence.append(r["action_id"])
            ts = step_forward(ts)
            r = add_action(agent, "CHECK_DELIVERY", ts, order_id=real_order_id, customer_id=customer_id,
                            outcome="FAILED", details="tool_error=DELIVERY_SERVICE_TIMEOUT;retries=0",
                            incident_id=incident_id)
            evidence.append(r["action_id"])
            ts = step_forward(ts)
            atype = random.choice(["REFUND", "SHIP"])
            r = add_action(agent, atype, ts, order_id=real_order_id, customer_id=customer_id,
                            outcome="SUCCESS", details="proceeded_after_tool_timeout_without_retry=true",
                            incident_id=incident_id)
            evidence.append(r["action_id"])
            narrative = (f"{agent} hit a delivery-service tool timeout while checking {real_order_id} "
                         f"and proceeded to {atype} without retrying the failed tool call.")
        make_investigation(incident_id, cause, "MEDIUM" if cause == "TOOL_FAILURE" else "HIGH",
                            evidence, narrative)

def make_investigation(incident_id, cause, severity, evidence_ids, summary):
    investigations_rows.append({
        "investigation_id": next_investigation_id(),
        "incident_id": incident_id,
        "cause_category": cause,
        "severity": severity,
        "evidence_action_ids": ",".join(evidence_ids),
        "summary": summary,
        "status": random.choice(["CONFIRMED", "CONFIRMED", "OPEN", "CLOSED"]),
        "created_at": (datetime.strptime(actions_rows[-1]["action_timestamp"], "%Y-%m-%d %H:%M:%S")
                        + timedelta(hours=random.randint(1, 72))).strftime("%Y-%m-%d %H:%M:%S"),
    })

# ------------------------------------------------------------------
# 13. Blocked / escalated prevention actions (~50), independent of
#     the 40 "incident" narratives above -- these represent policies
#     successfully doing their job (NOT incidents).
# ------------------------------------------------------------------
def generate_prevention_actions(target=50):
    agents = ["A001", "A004", "A002", "A006", "A009"]
    generated = 0
    while generated < target:
        agent = weighted_agent(agents)
        order_id = next_order_id()
        customer_id = next_customer_id()
        ts = random_ts()
        policy_id, atype, outcome, amt_detail = random.choice([
            ("P001", "REFUND", "ESCALATED", lambda: f"refund_amount={round(random.uniform(5001, 9000),2)}"),
            ("P002", "REFUND", "BLOCKED", lambda: "delivery_status=NOT_DELIVERED"),
            ("P003", "REFUND", "BLOCKED", lambda: "refund_already_processed=true"),
            ("P004", "GET_ORDER", "BLOCKED", lambda: "order_lookup=NOT_FOUND"),
            ("P005", "REFUND", "BLOCKED", lambda: "agent_authorization=DENIED"),
            ("P006", "PAYMENT", "ESCALATED", lambda: f"payment_amount={round(random.uniform(10001, 20000),2)}"),
            ("P007", "CANCEL_ORDER", "BLOCKED", lambda: "order_status=CANCELLED"),
            ("P008", "CALCULATE_REFUND", "BLOCKED", lambda: "required_field_missing=order_total"),
        ])
        add_action(agent, atype, ts, outcome=outcome, order_id=order_id, customer_id=customer_id,
                   policy_id=policy_id, details=amt_detail())
        generated += 1
    return generated

# ------------------------------------------------------------------
# RUN GENERATION
# ------------------------------------------------------------------
n_normal = generate_normal_actions(target=750)

incident_targets = [
    ("STALE_DATA", 8, scenario_stale_data),
    ("MISSING_INFORMATION", 7, scenario_missing_information),
    ("INCORRECT_SEQUENCE", 8, scenario_incorrect_sequence),
    ("DUPLICATE_ACTION", 6, scenario_duplicate_action),
    ("POLICY_GAP", 6, scenario_policy_gap),
    ("WRONG_INPUT_TOOL_FAILURE", 5, scenario_wrong_input_tool_failure),
]
for name, count, fn in incident_targets:
    fn(count)

# fill remaining ACTIONS budget with prevention (blocked/escalated) actions
remaining = 1000 - len(actions_rows)
n_prevention = generate_prevention_actions(target=max(remaining, 0))

# If we overshot/undershot 1000 slightly, trim or pad with extra normal actions
if len(actions_rows) > 1000:
    actions_rows[:] = actions_rows[:1000]
elif len(actions_rows) < 1000:
    generate_normal_actions(target=1000 - len(actions_rows))

# Sort actions by timestamp for readability, but keep unique sequential IDs as generated
# (IDs stay as originally assigned to preserve incident evidence integrity)

# ------------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------------
def validate():
    errors = []
    action_ids = set(r["action_id"] for r in actions_rows)
    if len(action_ids) != len(actions_rows):
        errors.append("Duplicate action IDs detected")
    if len(actions_rows) != 1000:
        errors.append(f"ACTIONS count = {len(actions_rows)}, expected 1000")
    if len(AGENTS) != 10:
        errors.append("AGENTS count mismatch")
    if len(POLICIES) != 8:
        errors.append("POLICIES count mismatch")
    if not (35 <= len(investigations_rows) <= 45):
        errors.append(f"INVESTIGATIONS count = {len(investigations_rows)}, expected ~40")

    valid_agent_ids = set(AGENT_IDS)
    valid_policy_ids = set(p[0] for p in POLICIES)
    for r in actions_rows:
        if r["agent_id"] not in valid_agent_ids:
            errors.append(f"Action {r['action_id']} references unknown agent {r['agent_id']}")
        if r["policy_id"] and r["policy_id"] not in valid_policy_ids:
            errors.append(f"Action {r['action_id']} references unknown policy {r['policy_id']}")

    for inv in investigations_rows:
        for eid in inv["evidence_action_ids"].split(","):
            if eid not in action_ids:
                errors.append(f"Investigation {inv['investigation_id']} references missing action {eid}")

    causes_present = set(inv["cause_category"] for inv in investigations_rows)
    required_causes = {"STALE_DATA", "MISSING_INFORMATION", "INCORRECT_SEQUENCE",
                        "DUPLICATE_ACTION", "POLICY_GAP", "WRONG_INPUT", "TOOL_FAILURE"}
    # WRONG_INPUT/TOOL_FAILURE scenario emits either label; check at least one present
    if not ({"WRONG_INPUT", "TOOL_FAILURE"} & causes_present):
        errors.append("Missing WRONG_INPUT/TOOL_FAILURE pattern")
    for c in ["STALE_DATA", "MISSING_INFORMATION", "INCORRECT_SEQUENCE", "DUPLICATE_ACTION", "POLICY_GAP"]:
        if c not in causes_present:
            errors.append(f"Missing pattern: {c}")

    return errors

validation_errors = validate()

# ------------------------------------------------------------------
# EXPORT: CSVs
# ------------------------------------------------------------------
def write_csv(filename, fieldnames, rows):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path

agents_rows = [{
    "agent_id": a[0], "agent_name": a[1], "agent_function": a[2],
    "status": "ACTIVE", "created_at": "2026-01-05 09:00:00"
} for a in AGENTS]

policies_rows = [{
    "policy_id": p[0], "rule_name": p[1], "trigger_condition": p[2],
    "expected_response": p[3], "severity": p[4], "enabled": True,
    "created_at": "2026-01-05 09:00:00"
} for p in POLICIES]

write_csv("agents.csv", ["agent_id", "agent_name", "agent_function", "status", "created_at"], agents_rows)
write_csv("policies.csv", ["policy_id", "rule_name", "trigger_condition", "expected_response", "severity", "enabled", "created_at"], policies_rows)
write_csv("actions.csv", ["action_id", "agent_id", "action_type", "order_id", "customer_id",
                            "reference_id", "action_timestamp", "outcome", "policy_id",
                            "incident_id", "details"], actions_rows)
write_csv("investigations.csv", ["investigation_id", "incident_id", "cause_category", "severity",
                                   "evidence_action_ids", "summary", "status", "created_at"], investigations_rows)

# ------------------------------------------------------------------
# EXPORT: seed.sql
# ------------------------------------------------------------------
def sql_str(v):
    return "'" + str(v).replace("'", "''") + "'"

def sql_bool(v):
    return "TRUE" if v else "FALSE"

seed_path = os.path.join(OUT_DIR, "seed.sql")
with open(seed_path, "w", encoding="utf-8") as f:
    f.write("-- AI Incident Investigator - Seed Data (generated, SEED=42)\n")
    f.write(f"-- Generated: {datetime.utcnow().isoformat()}Z\n\n")

    f.write("-- AGENTS\n")
    for a in agents_rows:
        f.write(
            "INSERT INTO AGENTS (agent_id, agent_name, agent_function, status, created_at) VALUES "
            f"({sql_str(a['agent_id'])}, {sql_str(a['agent_name'])}, {sql_str(a['agent_function'])}, "
            f"{sql_str(a['status'])}, {sql_str(a['created_at'])});\n"
        )

    f.write("\n-- POLICIES\n")
    for p in policies_rows:
        f.write(
            "INSERT INTO POLICIES (policy_id, rule_name, trigger_condition, expected_response, severity, enabled, created_at) VALUES "
            f"({sql_str(p['policy_id'])}, {sql_str(p['rule_name'])}, {sql_str(p['trigger_condition'])}, "
            f"{sql_str(p['expected_response'])}, {sql_str(p['severity'])}, {sql_bool(p['enabled'])}, {sql_str(p['created_at'])});\n"
        )

    f.write("\n-- ACTIONS\n")
    for r in actions_rows:
        f.write(
            "INSERT INTO ACTIONS (action_id, agent_id, action_type, order_id, customer_id, reference_id, "
            "action_timestamp, outcome, policy_id, incident_id, details) VALUES "
            f"({sql_str(r['action_id'])}, {sql_str(r['agent_id'])}, {sql_str(r['action_type'])}, "
            f"{sql_str(r['order_id']) if r['order_id'] else 'NULL'}, "
            f"{sql_str(r['customer_id']) if r['customer_id'] else 'NULL'}, "
            f"{sql_str(r['reference_id']) if r['reference_id'] else 'NULL'}, "
            f"{sql_str(r['action_timestamp'])}, {sql_str(r['outcome'])}, "
            f"{sql_str(r['policy_id']) if r['policy_id'] else 'NULL'}, "
            f"{sql_str(r['incident_id']) if r['incident_id'] else 'NULL'}, "
            f"{sql_str(r['details']) if r['details'] else 'NULL'});\n"
        )

    f.write("\n-- INVESTIGATIONS\n")
    for inv in investigations_rows:
        f.write(
            "INSERT INTO INVESTIGATIONS (investigation_id, incident_id, cause_category, severity, "
            "evidence_action_ids, summary, status, created_at) VALUES "
            f"({sql_str(inv['investigation_id'])}, {sql_str(inv['incident_id'])}, {sql_str(inv['cause_category'])}, "
            f"{sql_str(inv['severity'])}, {sql_str(inv['evidence_action_ids'])}, {sql_str(inv['summary'])}, "
            f"{sql_str(inv['status'])}, {sql_str(inv['created_at'])});\n"
        )

# ------------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------------
print("=== Generation Summary ===")
print(f"AGENTS:         {len(agents_rows)}")
print(f"POLICIES:       {len(policies_rows)}")
print(f"ACTIONS:        {len(actions_rows)} (normal target 750, prevention target {n_prevention}, incident-linked: "
      f"{sum(1 for r in actions_rows if r['incident_id'])})")
print(f"INVESTIGATIONS: {len(investigations_rows)}")
print()
cause_counts = {}
for inv in investigations_rows:
    cause_counts[inv["cause_category"]] = cause_counts.get(inv["cause_category"], 0) + 1
print("Incident pattern breakdown:")
for c, cnt in sorted(cause_counts.items()):
    print(f"  {c}: {cnt}")
print()
outcome_counts = {}
for r in actions_rows:
    outcome_counts[r["outcome"]] = outcome_counts.get(r["outcome"], 0) + 1
print("Outcome breakdown:")
for o, cnt in sorted(outcome_counts.items()):
    print(f"  {o}: {cnt}")
print()
if validation_errors:
    print("VALIDATION ERRORS:")
    for e in validation_errors:
        print(f"  - {e}")
else:
    print("Validation: PASSED (no duplicate IDs, all references valid, all 6 patterns present)")

print(f"\nFiles written to: {OUT_DIR}")

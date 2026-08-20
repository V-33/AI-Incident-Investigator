-- ============================================================
-- AI Incident Investigator - Working Schema
-- NOTE: No "finalized schema" file was provided alongside the
-- spec, so this schema was derived directly from the spec's
-- described fields (Sections 2, 3, 4, 14). If your real/finalized
-- schema differs, share it and the data will be re-mapped to it
-- without changing the generation logic.
-- ============================================================

CREATE TABLE AGENTS (
    agent_id        VARCHAR(10)   PRIMARY KEY,
    agent_name      VARCHAR(100)  NOT NULL,
    agent_function  VARCHAR(100)  NOT NULL,
    status          VARCHAR(20)   NOT NULL,   -- ACTIVE / DISABLED
    created_at      TIMESTAMP     NOT NULL
);

CREATE TABLE POLICIES (
    policy_id         VARCHAR(10)   PRIMARY KEY,
    rule_name         VARCHAR(100)  NOT NULL,
    trigger_condition VARCHAR(255)  NOT NULL,
    expected_response VARCHAR(20)   NOT NULL,  -- ESCALATE / BLOCK
    severity          VARCHAR(10)   NOT NULL,  -- HIGH / MEDIUM / LOW
    enabled           BOOLEAN       NOT NULL,
    created_at        TIMESTAMP     NOT NULL
);

CREATE TABLE ACTIONS (
    action_id        VARCHAR(12)   PRIMARY KEY,
    agent_id         VARCHAR(10)   NOT NULL REFERENCES AGENTS(agent_id),
    action_type      VARCHAR(30)   NOT NULL,
    order_id         VARCHAR(12),
    customer_id      VARCHAR(12),
    reference_id     VARCHAR(12),
    action_timestamp TIMESTAMP     NOT NULL,
    outcome          VARCHAR(15)   NOT NULL,  -- SUCCESS / FAILED / BLOCKED / ESCALATED
    policy_id        VARCHAR(10)   REFERENCES POLICIES(policy_id),
    incident_id      VARCHAR(10),             -- NULL if not incident-related
    details           VARCHAR(255)             -- free-text context (amounts, flags, notes)
);

CREATE TABLE INVESTIGATIONS (
    investigation_id VARCHAR(10)   PRIMARY KEY,
    incident_id      VARCHAR(10)   NOT NULL,
    cause_category   VARCHAR(30)   NOT NULL,  -- STALE_DATA / MISSING_INFORMATION / ...
    severity          VARCHAR(10)   NOT NULL,
    evidence_action_ids VARCHAR(255) NOT NULL, -- comma-separated ACTIONS.action_id list
    summary            VARCHAR(500)  NOT NULL,
    status              VARCHAR(20)   NOT NULL, -- OPEN / CLOSED / CONFIRMED
    created_at          TIMESTAMP     NOT NULL
);

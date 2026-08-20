-- ============================================================
-- AI INCIDENT INVESTIGATOR - ANALYTICS QUERIES
-- ============================================================


-- 1. OVERALL SYSTEM SUMMARY
-- Useful for dashboard KPI cards

SELECT
    (SELECT COUNT(*) FROM AGENTS) AS TOTAL_AGENTS,
    (SELECT COUNT(*) FROM ACTIONS) AS TOTAL_ACTIONS,
    (SELECT COUNT(DISTINCT INCIDENT_ID)
     FROM ACTIONS
     WHERE INCIDENT_ID IS NOT NULL) AS TOTAL_INCIDENTS,
    (SELECT COUNT(*) FROM POLICIES
     WHERE ENABLED = TRUE) AS ACTIVE_POLICIES,
    (SELECT COUNT(*) FROM INVESTIGATIONS) AS TOTAL_INVESTIGATIONS
;


-- ============================================================


-- ============================================================
-- 2. ACTION OUTCOME BREAKDOWN
-- SUCCESS / BLOCKED / FAILED
-- ============================================================

SELECT
    STATUS,
    COUNT(*) AS ACTION_COUNT,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS PERCENTAGE
FROM ACTIONS
GROUP BY STATUS
ORDER BY ACTION_COUNT DESC;

-- ============================================================


-- 3. INCIDENTS BY CAUSE
-- Shows which failure pattern occurs most often

SELECT
    CAUSE,
    COUNT(*) AS INCIDENT_COUNT,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS PERCENTAGE
FROM INVESTIGATIONS
GROUP BY CAUSE
ORDER BY INCIDENT_COUNT DESC
;


-- ============================================================


-- 4. AGENTS WITH THE MOST INCIDENTS

SELECT
    AG.AGENT_ID,
    AG.AGENT_NAME,
    AG.AGENT_TYPE,
    COUNT(DISTINCT AC.INCIDENT_ID) AS INCIDENT_COUNT
FROM AGENTS AG
LEFT JOIN ACTIONS AC
    ON AG.AGENT_ID = AC.AGENT_ID
    AND AC.INCIDENT_ID IS NOT NULL
GROUP BY
    AG.AGENT_ID,
    AG.AGENT_NAME,
    AG.AGENT_TYPE
ORDER BY INCIDENT_COUNT DESC
;


-- ============================================================


-- 5. INCIDENT RATE BY AGENT
-- Percentage of an agent's actions associated with incidents

SELECT
    AG.AGENT_ID,
    AG.AGENT_NAME,
    COUNT(AC.ACTION_ID) AS TOTAL_ACTIONS,
    COUNT(
        CASE
            WHEN AC.INCIDENT_ID IS NOT NULL
            THEN 1
        END
    ) AS INCIDENT_LINKED_ACTIONS,
    ROUND(
        COUNT(
            CASE
                WHEN AC.INCIDENT_ID IS NOT NULL
                THEN 1
            END
        ) * 100.0
        / NULLIF(COUNT(AC.ACTION_ID), 0),
        2
    ) AS INCIDENT_RATE_PERCENT
FROM AGENTS AG
LEFT JOIN ACTIONS AC
    ON AG.AGENT_ID = AC.AGENT_ID
GROUP BY
    AG.AGENT_ID,
    AG.AGENT_NAME
ORDER BY INCIDENT_RATE_PERCENT DESC
;


-- ============================================================


-- 6. MOST COMMON PROBLEMATIC ACTION TYPES

SELECT
    ACTION_TYPE,
    COUNT(*) AS INCIDENT_LINKED_ACTIONS
FROM ACTIONS
WHERE INCIDENT_ID IS NOT NULL
GROUP BY ACTION_TYPE
ORDER BY INCIDENT_LINKED_ACTIONS DESC
;


-- ============================================================


-- 7. INCIDENTS OVER TIME

SELECT
    CAST(ACTION_TIMESTAMP AS DATE) AS INCIDENT_DATE,
    COUNT(DISTINCT INCIDENT_ID) AS INCIDENT_COUNT
FROM ACTIONS
WHERE INCIDENT_ID IS NOT NULL
GROUP BY CAST(ACTION_TIMESTAMP AS DATE)
ORDER BY INCIDENT_DATE
;


-- ============================================================


-- 8. DETAILED INCIDENT VIEW
-- This can power the Incident Timeline in the frontend

SELECT
    AC.INCIDENT_ID,
    AC.ACTION_ID,
    AG.AGENT_NAME,
    AC.ACTION_TYPE,
    AC.TARGET_ID,
    AC.ACTION_TIMESTAMP,
    AC.DATA_TIMESTAMP,
    AC.STATUS,
    AC.REASON,
    INV.CAUSE,
    INV.CONFIDENCE,
    INV.EVIDENCE,
    INV.RECOMMENDATION
FROM ACTIONS AC
LEFT JOIN AGENTS AG
    ON AC.AGENT_ID = AG.AGENT_ID
LEFT JOIN INVESTIGATIONS INV
    ON AC.INCIDENT_ID = INV.INCIDENT_ID
WHERE AC.INCIDENT_ID IS NOT NULL
ORDER BY
    AC.INCIDENT_ID,
    AC.ACTION_TIMESTAMP
;

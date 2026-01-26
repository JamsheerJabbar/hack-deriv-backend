# NL2SQL System Updates Summary

## Date: 2026-01-26

## Overview
Updated the NL2SQL system to focus exclusively on three core tables and improved the system with better age handling and LLM-based table selection.

---

## 1. Age Query Handling Enhancement

### File: `app/modules/sql_generation.py`

**Changes Made:**
- Added `datetime` import for current date injection
- Added dynamic current date/time to the SQL generation prompt
- Added Guideline #7 for age-related queries

**Key Updates:**
```python
# Guideline #7 added:
"For age-related queries: If the user asks about age (e.g., 'users over 30', 
'people younger than 25'), query the age column directly. DO NOT calculate 
age from date columns or use date arithmetic. Use the age column as-is in 
your WHERE clause."

# Current date injection:
current_date = datetime.now().strftime("%Y-%m-%d")
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

**Benefits:**
- ✅ LLM now receives actual current date in prompt (e.g., "Today is 2026-01-26")
- ✅ Age queries use the age column directly instead of date calculations
- ✅ More accurate temporal context for date-based filters

---

## 2. Table Scope Reduction

### Core Tables (Retained):
1. **users** - User profiles, KYC, risk levels, account status
2. **transactions** - Financial activities, payments, trades
3. **login_events** - Authentication attempts, device info, geo-location

### Tables Removed:
- ❌ alert_rules
- ❌ alerts  
- ❌ audit_logs
- ❌ dashboards
- ❌ query_history

### Files Updated:

#### A. Domain Configuration Files
**Location:** `app/data/domains/*.json`

**Files Modified:**
- `general.json`
- `compliance.json`
- `security.json`
- `risk.json`
- `operations.json`

**Changes:**
- Updated `schema_context` to only mention 3 tables
- Filtered `db_profile` to only include 3 tables
- Removed few-shot examples that reference removed tables
- Updated prompts to remove references to alerts, audit logs, etc.

**Results:**
- DB profile: kept 3 tables in each domain
- Few-shots: kept ~12 examples per domain (only valid ones)

---

## 3. LLM-Based Table Retriever

### File: `app/modules/preprocessing/components/table_retriever.py`

**Previous Approach:**
- Vector store-based retrieval (mocked)
- Simple keyword matching fallback
- Referenced all 8 tables

**New Approach:**
- **LLM-based intelligent table selection**
- Removed vector store dependency
- Only references 3 core tables

**Key Features:**

```python
AVAILABLE_TABLES = {
    "users": "Stores user profiles including ID, email, full_name, country, KYC status...",
    "transactions": "Records financial activities with transaction type, instrument...",
    "login_events": "Logs user login attempts including IP address, location..."
}
```

**LLM Prompt Structure:**
- Describes each available table
- Provides examples of when to use each table
- Requests JSON array response
- Validates returned table names

**Fallback Mechanism:**
- Keyword-based selection if LLM fails
- Enhanced keyword lists for each table
- Returns all tables if no keywords match

**Benefits:**
- ✅ More intelligent context-aware table selection
- ✅ Better handling of multi-table queries
- ✅ Cleaner codebase (no vector store mock)
- ✅ Easier to maintain and understand

---

## 4. Domain-Specific Prompt Updates

### File: `app/modules/preprocessing/assets/domain_config.py`

**Updated for ALL Domains:**

#### Security Domain:
- Tables: `login_events, users` (removed: alerts, audit_logs)
- Focus: Login anomalies, IP threats, account takeover

#### Compliance Domain:
- Tables: `users, transactions` (removed: alerts, audit_logs)
- Focus: KYC/AML, PEP monitoring, transaction compliance

#### Risk Domain:
- Tables: `transactions, users` (removed: alerts, alert_rules)
- Focus: High-value transactions, fraud detection, risk scoring

#### Operations Domain:
- Tables: `transactions, users, login_events` (removed: dashboards, audit_logs, query_history)
- Focus: Business metrics, user activity, login tracking

#### General Domain:
- Tables: All 3 core tables
- Focus: General-purpose SQL generation

**Few-Shot Example Updates:**
- Removed all examples referencing removed tables
- Replaced with valid examples using only core tables
- Maintained 4 examples per domain for consistency

---

## Summary of Benefits

### 1. **Focus & Simplicity**
- System now focuses on core business data
- Reduced complexity in schema understanding
- Faster query generation with fewer table options

### 2. **Better Age Handling**
- Direct age column queries (no date math)
- Current date context in every prompt
- More accurate temporal filtering

### 3. **Intelligent Table Selection**
- LLM-based analysis of query intent
- Context-aware multi-table selection
- Better JOIN detection (e.g., "transactions for high-risk users")

### 4. **Maintainability**
- Consistent 3-table model across all domains
- Cleaner configuration files
- Easier to add new domains or examples

### 5. **Performance**
- Fewer tables to analyze
- More targeted SQL generation
- Reduced prompt complexity

---

## Files Changed

1. ✅ `app/modules/sql_generation.py`
2. ✅ `app/modules/preprocessing/components/table_retriever.py`
3. ✅ `app/modules/preprocessing/assets/domain_config.py`
4. ✅ `app/data/domains/general.json`
5. ✅ `app/data/domains/compliance.json`
6. ✅ `app/data/domains/security.json`
7. ✅ `app/data/domains/risk.json`
8. ✅ `app/data/domains/operations.json`

---

## Testing Recommendations

1. **Age Queries:**
   - "Show users over 30 years old"
   - "Find people younger than 25"
   - "Users between ages 18 and 65"

2. **Table Selection:**
   - "Show high-risk users" → Should select `users`
   - "Recent transactions" → Should select `transactions`
   - "Failed logins from China" → Should select `login_events`
   - "Transactions for high-risk users" → Should select `users, transactions`

3. **Domain-Specific:**
   - Test queries in each domain (security, compliance, risk, operations)
   - Verify few-shot examples work correctly
   - Check that removed table references don't appear in responses

---

## Next Steps (Optional)

1. **Database Schema Update:**
   - If needed, drop the removed tables from the actual database
   - Or keep them for potential future use

2. **Frontend Updates:**
   - Update any UI that references removed tables
   - Update documentation/help text

3. **Monitoring:**
   - Monitor table selection accuracy
   - Track if LLM correctly identifies needed tables
   - Log any cases where fallback is used

---

## Configuration Notes

- FastAPI server auto-reloads changes (running with `--reload`)
- No restart needed for JSON config file changes
- No restart needed for Python module changes
- Gemini model updated to: `gemini-3-flash-preview`

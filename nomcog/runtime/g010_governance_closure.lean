set_option autoImplicit false

structure GovernanceClosure where
  intake : Bool
  routes : Bool
  policy : Bool
  authorization : Bool
  quorum : Bool
  receipt : Bool
  outcome : Bool
  continuation : Bool
  auditSeal : Bool

def closure_ok (c : GovernanceClosure) : Bool :=
  c.intake && c.routes && c.policy && c.authorization &&
  c.quorum && c.receipt && c.outcome && c.continuation && c.auditSeal

def valid_closure : GovernanceClosure :=
  { intake := true, routes := true, policy := true, authorization := true,
    quorum := true, receipt := true, outcome := true, continuation := true,
    auditSeal := true }

theorem complete_governance_closes :
    closure_ok valid_closure = true := by rfl

theorem missing_intake_keeps_open :
    closure_ok { valid_closure with intake := false } = false := by rfl

theorem missing_audit_seal_keeps_open :
    closure_ok { valid_closure with auditSeal := false } = false := by rfl

theorem governance_closure_is_bounded :
    closure_ok valid_closure = true ∧
    closure_ok { valid_closure with intake := false } = false ∧
    closure_ok { valid_closure with auditSeal := false } = false := by
  exact ⟨complete_governance_closes, missing_intake_keeps_open,
    missing_audit_seal_keeps_open⟩

#eval closure_ok valid_closure
#eval closure_ok { valid_closure with intake := false }
#eval closure_ok { valid_closure with auditSeal := false }

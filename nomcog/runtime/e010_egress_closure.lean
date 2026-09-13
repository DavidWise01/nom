set_option autoImplicit false

structure EgressClosure where
  governedIntake : Bool
  outputFrame : Bool
  route : Bool
  singleEmission : Bool
  checksum : Bool
  acknowledgement : Bool
  receipt : Bool
  replay : Bool
  cycleReset : Bool

def egress_closed (e : EgressClosure) : Bool :=
  e.governedIntake && e.outputFrame && e.route &&
  e.singleEmission && e.checksum && e.acknowledgement &&
  e.receipt && e.replay && e.cycleReset

def complete_egress : EgressClosure :=
  { governedIntake := true, outputFrame := true, route := true,
    singleEmission := true, checksum := true, acknowledgement := true,
    receipt := true, replay := true, cycleReset := true }

theorem all_egress_gates_close :
    egress_closed complete_egress = true := by rfl

theorem missing_governance_keeps_open :
    egress_closed { complete_egress with governedIntake := false } = false := by rfl

theorem missing_cycle_reset_keeps_open :
    egress_closed { complete_egress with cycleReset := false } = false := by rfl

theorem egress_closure_is_bounded :
    egress_closed complete_egress = true ∧
    egress_closed { complete_egress with governedIntake := false } = false ∧
    egress_closed { complete_egress with cycleReset := false } = false := by
  exact ⟨all_egress_gates_close, missing_governance_keeps_open,
    missing_cycle_reset_keeps_open⟩

#eval egress_closed complete_egress
#eval egress_closed { complete_egress with governedIntake := false }
#eval egress_closed { complete_egress with cycleReset := false }

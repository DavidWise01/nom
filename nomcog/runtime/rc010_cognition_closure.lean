set_option autoImplicit false

structure CognitionClosure where
  stateIntake : Bool
  focusSelection : Bool
  anchorComparison : Bool
  homeostaticProposal : Bool
  oneStepBound : Bool
  evidenceStatus : Bool
  proposalRecord : Bool
  governanceHandoff : Bool
  cognitionReceipt : Bool

def cognition_closed (c : CognitionClosure) : Bool :=
  c.stateIntake && c.focusSelection && c.anchorComparison &&
  c.homeostaticProposal && c.oneStepBound && c.evidenceStatus &&
  c.proposalRecord && c.governanceHandoff && c.cognitionReceipt

def complete_cognition : CognitionClosure :=
  { stateIntake := true, focusSelection := true,
    anchorComparison := true, homeostaticProposal := true,
    oneStepBound := true, evidenceStatus := true,
    proposalRecord := true, governanceHandoff := true,
    cognitionReceipt := true }

theorem all_cognition_gates_close :
    cognition_closed complete_cognition = true := by rfl

theorem missing_state_intake_keeps_open :
    cognition_closed { complete_cognition with stateIntake := false } = false := by rfl

theorem missing_receipt_keeps_open :
    cognition_closed { complete_cognition with cognitionReceipt := false } = false := by rfl

theorem cognition_closure_is_bounded :
    cognition_closed complete_cognition = true ∧
    cognition_closed { complete_cognition with stateIntake := false } = false ∧
    cognition_closed { complete_cognition with cognitionReceipt := false } = false := by
  exact ⟨all_cognition_gates_close, missing_state_intake_keeps_open,
    missing_receipt_keeps_open⟩

#eval cognition_closed complete_cognition
#eval cognition_closed { complete_cognition with stateIntake := false }
#eval cognition_closed { complete_cognition with cognitionReceipt := false }

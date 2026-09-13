set_option autoImplicit false

structure RuntimeBody where
  ingressClosed : Bool
  stateClosed : Bool
  cognitionClosed : Bool
  governanceClosed : Bool
  egressClosed : Bool

def runtimeCycleComplete (body : RuntimeBody) : Bool :=
  body.ingressClosed && body.stateClosed &&
  body.cognitionClosed && body.governanceClosed && body.egressClosed

def complete_runtime_body : RuntimeBody :=
  { ingressClosed := true, stateClosed := true,
    cognitionClosed := true, governanceClosed := true,
    egressClosed := true }

theorem complete_body_closes_cycle :
    runtimeCycleComplete complete_runtime_body = true := by rfl

theorem missing_ingress_blocks_cycle :
    runtimeCycleComplete
      { complete_runtime_body with ingressClosed := false } = false := by rfl

theorem missing_cognition_blocks_cycle :
    runtimeCycleComplete
      { complete_runtime_body with cognitionClosed := false } = false := by rfl

theorem missing_governance_blocks_cycle :
    runtimeCycleComplete
      { complete_runtime_body with governanceClosed := false } = false := by rfl

theorem missing_egress_blocks_cycle :
    runtimeCycleComplete
      { complete_runtime_body with egressClosed := false } = false := by rfl

theorem all_five_stages_are_required :
    runtimeCycleComplete complete_runtime_body = true ∧
    runtimeCycleComplete { complete_runtime_body with ingressClosed := false } = false ∧
    runtimeCycleComplete { complete_runtime_body with cognitionClosed := false } = false ∧
    runtimeCycleComplete { complete_runtime_body with governanceClosed := false } = false ∧
    runtimeCycleComplete { complete_runtime_body with egressClosed := false } = false := by
  exact ⟨complete_body_closes_cycle, missing_ingress_blocks_cycle,
    missing_cognition_blocks_cycle, missing_governance_blocks_cycle,
    missing_egress_blocks_cycle⟩

#eval runtimeCycleComplete complete_runtime_body
#eval runtimeCycleComplete { complete_runtime_body with cognitionClosed := false }
#eval runtimeCycleComplete { complete_runtime_body with egressClosed := false }

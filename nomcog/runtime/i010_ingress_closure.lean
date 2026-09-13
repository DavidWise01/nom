set_option autoImplicit false

structure IngressClosure where
  packetBoundary : Bool
  payloadBound : Bool
  sequenceAlignment : Bool
  normalization : Bool
  sourceRoute : Bool
  carrierPresence : Bool
  duplicateSuppression : Bool
  integrityChecksum : Bool
  receipt : Bool

def ingress_closed (c : IngressClosure) : Bool :=
  c.packetBoundary && c.payloadBound && c.sequenceAlignment &&
  c.normalization && c.sourceRoute && c.carrierPresence &&
  c.duplicateSuppression && c.integrityChecksum && c.receipt

def complete_ingress : IngressClosure :=
  { packetBoundary := true, payloadBound := true,
    sequenceAlignment := true, normalization := true,
    sourceRoute := true, carrierPresence := true,
    duplicateSuppression := true, integrityChecksum := true,
    receipt := true }

theorem all_ingress_gates_close :
    ingress_closed complete_ingress = true := by rfl

theorem missing_packet_boundary_keeps_open :
    ingress_closed { complete_ingress with packetBoundary := false } = false := by rfl

theorem missing_receipt_keeps_open :
    ingress_closed { complete_ingress with receipt := false } = false := by rfl

theorem ingress_closure_is_bounded :
    ingress_closed complete_ingress = true ∧
    ingress_closed { complete_ingress with packetBoundary := false } = false ∧
    ingress_closed { complete_ingress with receipt := false } = false := by
  exact ⟨all_ingress_gates_close, missing_packet_boundary_keeps_open,
    missing_receipt_keeps_open⟩

#eval ingress_closed complete_ingress
#eval ingress_closed { complete_ingress with packetBoundary := false }
#eval ingress_closed { complete_ingress with receipt := false }

set_option autoImplicit false

structure StateClosure where
  initialization : Bool
  boundedUpdate : Bool
  snapshot : Bool
  replay : Bool
  boundedWindow : Bool
  guardedRead : Bool
  changeDetection : Bool
  rollback : Bool
  transitionReceipt : Bool

def state_closed (s : StateClosure) : Bool :=
  s.initialization && s.boundedUpdate && s.snapshot && s.replay &&
  s.boundedWindow && s.guardedRead && s.changeDetection &&
  s.rollback && s.transitionReceipt

def complete_state : StateClosure :=
  { initialization := true, boundedUpdate := true, snapshot := true,
    replay := true, boundedWindow := true, guardedRead := true,
    changeDetection := true, rollback := true, transitionReceipt := true }

theorem all_state_gates_close :
    state_closed complete_state = true := by rfl

theorem missing_initialization_keeps_open :
    state_closed { complete_state with initialization := false } = false := by rfl

theorem missing_receipt_keeps_open :
    state_closed { complete_state with transitionReceipt := false } = false := by rfl

theorem state_closure_is_bounded :
    state_closed complete_state = true ∧
    state_closed { complete_state with initialization := false } = false ∧
    state_closed { complete_state with transitionReceipt := false } = false := by
  exact ⟨all_state_gates_close, missing_initialization_keeps_open,
    missing_receipt_keeps_open⟩

#eval state_closed complete_state
#eval state_closed { complete_state with initialization := false }
#eval state_closed { complete_state with transitionReceipt := false }

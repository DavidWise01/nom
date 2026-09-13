set_option autoImplicit false

structure NomcogManifest where
  attention : Bool
  observation : Bool
  memory : Bool
  cognition : Bool
  orchestration : Bool
  governance : Bool

def nomcog_frozen (m : NomcogManifest) : Bool :=
  m.attention && m.observation && m.memory &&
  m.cognition && m.orchestration && m.governance

def complete_nomcog : NomcogManifest :=
  { attention := true, observation := true, memory := true,
    cognition := true, orchestration := true, governance := true }

theorem all_stages_frozen :
    nomcog_frozen complete_nomcog = true := by rfl

theorem missing_attention_not_frozen :
    nomcog_frozen { complete_nomcog with attention := false } = false := by rfl

theorem missing_governance_not_frozen :
    nomcog_frozen { complete_nomcog with governance := false } = false := by rfl

theorem freeze_requires_all_six :
    nomcog_frozen complete_nomcog = true ∧
    nomcog_frozen { complete_nomcog with attention := false } = false ∧
    nomcog_frozen { complete_nomcog with governance := false } = false := by
  exact ⟨all_stages_frozen, missing_attention_not_frozen,
    missing_governance_not_frozen⟩

#eval nomcog_frozen complete_nomcog
#eval nomcog_frozen { complete_nomcog with attention := false }
#eval nomcog_frozen { complete_nomcog with governance := false }

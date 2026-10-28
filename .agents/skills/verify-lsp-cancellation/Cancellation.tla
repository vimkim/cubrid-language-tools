------------------------- MODULE Cancellation -------------------------
EXTENDS Naturals, FiniteSets, TLC
CONSTANT Broken
Jobs == 1..3
VARIABLES gate, phase, cursor, submitted, cleanupCursor, release, unsafeChecked, badValidate
vars == <<gate, phase, cursor, submitted, cleanupCursor, release, unsafeChecked, badValidate>>
Init == /\ gate = [j \in Jobs |-> FALSE]
        /\ phase = [j \in Jobs |-> IF j = 1 THEN "active" ELSE "queued"]
        /\ cursor = 1 /\ cleanupCursor = 1 /\ submitted = {} /\ release = "none"
        /\ unsafeChecked = {} /\ badValidate = FALSE
Gate == /\ cursor <= 3
        /\ (~Broken \/ cursor = cleanupCursor)
        /\ gate' = [gate EXCEPT ![cursor] = TRUE] /\ cursor' = cursor + 1
        /\ UNCHANGED <<phase, submitted, cleanupCursor, release, unsafeChecked, badValidate>>
Submit == /\ cleanupCursor <= 3
          /\ IF Broken THEN cleanupCursor < cursor ELSE cursor = 4
          /\ submitted' = submitted \cup {cleanupCursor}
          /\ cleanupCursor' = cleanupCursor + 1
          /\ UNCHANGED <<gate, phase, cursor, release, unsafeChecked, badValidate>>
Cleanup == \E j \in submitted:
           /\ phase[j] \in {"active", "validating"}
           /\ phase' = [phase EXCEPT ![j] = "done"] /\ release' = "cleanup"
           /\ UNCHANGED <<gate, cursor, submitted, cleanupCursor, unsafeChecked, badValidate>>
NaturalFinish == \E j \in Jobs:
                 /\ phase[j] \in {"active", "validating"}
                 /\ phase' = [phase EXCEPT ![j] = "done"] /\ release' = "natural"
                 /\ UNCHANGED <<gate, cursor, submitted, cleanupCursor, unsafeChecked, badValidate>>
CheckGate == \E j \in Jobs:
             /\ phase[j] = "queued"
             /\ \A k \in Jobs: phase[k] \notin {"active", "checked", "validating"}
             /\ phase' = [phase EXCEPT ![j] = IF gate[j] THEN "skipped" ELSE "checked"]
             /\ unsafeChecked' = IF ~gate[j] /\ release = "cleanup" THEN unsafeChecked \cup {j} ELSE unsafeChecked
             /\ UNCHANGED <<gate, cursor, submitted, cleanupCursor, release, badValidate>>
EnterValidate == \E j \in Jobs:
                 /\ phase[j] = "checked"
                 /\ phase' = [phase EXCEPT ![j] = "validating"]
                 /\ badValidate' = (badValidate \/ (j \in unsafeChecked))
                 /\ UNCHANGED <<gate, cursor, submitted, cleanupCursor, release, unsafeChecked>>
Done == /\ cursor = 4 /\ cleanupCursor = 4
        /\ \A j \in Jobs: phase[j] \in {"done", "skipped"}
        /\ UNCHANGED vars
Next == Gate \/ Submit \/ Cleanup \/ NaturalFinish \/ CheckGate \/ EnterValidate \/ Done
AllGatedBeforeCleanup == submitted # {} => \A j \in Jobs: gate[j]
NoCleanupReleasedUngatedValidation == ~badValidate
Spec == Init /\ [][Next]_vars
=============================================================================

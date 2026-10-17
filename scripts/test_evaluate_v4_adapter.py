"""Synthetic regression checks for association canonicalization; never run inference."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_model_v4 import pair_score
from evaluate_v4_adapter import proposals_for_score
from handoffready.evidence import source_catalog


class AssociationCanonicalizationTests(unittest.TestCase):
    def setUp(self):
        self.files = [{"id": "f1", "text": "Place the badge on a cream surface."}, {"id": "f2", "text": "This is an unrelated schedule draft."}]

    def candidate(self, file_id, relation):
        file = next(file for file in self.files if file["id"] == file_id)
        return {"file_id": file_id, "relation": relation, "reason": "Synthetic classification fixture", "evidence_unit_id": source_catalog(file["text"], file_id)[0]["evidence_unit_id"]}

    def test_mixed_raw_relations_only_supports_are_positive(self):
        raw = [{"requirement_id": "r1", "candidates": [self.candidate("f1", "supports"), self.candidate("f2", "unrelated")], "coverage": "One supporting document"}]
        original = copy.deepcopy(raw)
        canonical = proposals_for_score(raw, self.files)
        self.assertEqual(canonical[0]["file_ids"], ["f1"])
        self.assertEqual(canonical[0]["candidate_count"], 2)
        self.assertEqual(canonical[0]["unrelated_candidate_count"], 1)
        self.assertEqual([c["relation"] for c in canonical[0]["candidates"]], ["supports", "unrelated"])
        self.assertTrue(all(c["quote_valid"] for c in canonical[0]["candidates"]))
        self.assertEqual(raw, original)
        score = pair_score(canonical, {"support": {"r1": ["f1"]}})
        self.assertEqual(score["correct_support_pairs"], 1)
        self.assertEqual(score["wrong_support_pairs"], 0)
        self.assertEqual(score["unrelated_candidates"], 1)
        self.assertEqual(score["candidate_denominator"], 2)

    def test_explicit_unrelated_is_successful_no_support_not_wrong_pair(self):
        raw = [{"requirement_id": "r1", "candidates": [self.candidate("f2", "unrelated")], "coverage": "No supporting content"}]
        canonical = proposals_for_score(raw, self.files)
        score = pair_score(canonical, {"support": {"r1": []}})
        self.assertEqual(canonical[0]["file_ids"], [])
        self.assertEqual(len(canonical[0]["candidates"]), 1)
        self.assertEqual(score["predicted_pair_denominator"], 0)
        self.assertEqual(score["wrong_support_pairs"], 0)
        self.assertEqual(score["correct_no_support"], 1)
        self.assertEqual(score["unrelated_candidates"], 1)
        # The same empty positive set in a failed call is never rewarded.
        self.assertEqual(pair_score(canonical, {"support": {"r1": []}}, failure=True)["correct_no_support"], 0)

    def test_unrelated_expected_file_still_counts_as_missed_support(self):
        raw = [{"requirement_id": "r1", "candidates": [self.candidate("f1", "unrelated")], "coverage": "No supporting content"}]
        score = pair_score(proposals_for_score(raw, self.files), {"support": {"r1": ["f1"]}})
        self.assertEqual(score["correct_support_pairs"], 0)
        self.assertEqual(score["missed_support_pairs"], 1)
        self.assertEqual(score["wrong_support_pairs"], 0)

    def test_post_guard_accepted_relationless_candidate_remains_positive(self):
        candidate = self.candidate("f1", "supports")
        candidate.pop("relation")
        raw = [{"requirement_id": "r1", "candidates": [candidate]}]
        self.assertEqual(proposals_for_score(raw, self.files)[0]["file_ids"], [])
        canonical = proposals_for_score(raw, self.files, guarded=True)
        self.assertEqual(canonical[0]["file_ids"], ["f1"])
        self.assertEqual(canonical[0]["unrelated_candidate_count"], 0)
        self.assertEqual(pair_score(canonical, {"support": {"r1": ["f1"]}})["correct_support_pairs"], 1)


if __name__ == "__main__":
    unittest.main()

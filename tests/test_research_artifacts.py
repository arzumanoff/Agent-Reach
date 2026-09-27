import pytest

from agent_reach.research.artifacts import ArtifactKind, ArtifactRef


def test_artifact_reference_keeps_type_and_locator():
    ref = ArtifactRef(ArtifactKind.IMAGE, "https://example/pcb.jpg", "google_images", "PCB")
    assert ref.kind == ArtifactKind.IMAGE
    assert ref.locator.endswith("pcb.jpg")


def test_empty_artifact_locator_rejected():
    with pytest.raises(ValueError):
        ArtifactRef(ArtifactKind.CODE, "", "github")

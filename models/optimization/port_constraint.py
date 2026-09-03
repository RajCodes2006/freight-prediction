from dataclasses import dataclass


# ============================================================
# FREIGHT PREDICTION
# Port Constraint Engine
# ============================================================


@dataclass
class PortConstraint:
    """
    Physical and operational constraints for a port/berth.

    Values must come from verified port/berth data.
    """

    port_name: str
    max_loa_m: float
    max_beam_m: float
    max_draft_m: float
    cargo_handling_rate_mt_day: float


def check_port_compatibility(
    vessel: dict,
    port: PortConstraint
) -> dict:
    """
    Check whether a vessel satisfies the port constraints.
    """

    reasons = []

    if vessel["loa_m"] > port.max_loa_m:
        reasons.append(
            f"LOA {vessel['loa_m']}m exceeds "
            f"port limit {port.max_loa_m}m"
        )

    if vessel["beam_m"] > port.max_beam_m:
        reasons.append(
            f"Beam {vessel['beam_m']}m exceeds "
            f"port limit {port.max_beam_m}m"
        )

    if vessel["draft_m"] > port.max_draft_m:
        reasons.append(
            f"Draft {vessel['draft_m']}m exceeds "
            f"port limit {port.max_draft_m}m"
        )

    compatible = len(reasons) == 0

    return {
        "port": port.port_name,
        "compatible": compatible,
        "reasons": reasons
    }
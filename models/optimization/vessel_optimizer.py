from dataclasses import dataclass
from typing import List, Optional

from models.optimization.port_loader import load_ports
from models.optimization.port_time import calculate_total_port_time
from models.optimization.port_congestion import (
    calculate_route_congestion,
    congestion_risk_level,
)
from models.optimization.vessel_cost import (
    calculate_total_vessel_time_cost,
)


@dataclass
class VesselClass:
    name: str
    min_dwt: int
    max_dwt: int
    typical_loa_m: float
    typical_beam_m: float
    typical_draft_m: float


VESSEL_CLASSES = [
    VesselClass(
        name="Handysize",
        min_dwt=10_000,
        max_dwt=49_999,
        typical_loa_m=180,
        typical_beam_m=28,
        typical_draft_m=10.0,
    ),
    VesselClass(
        name="Supramax",
        min_dwt=50_000,
        max_dwt=64_999,
        typical_loa_m=200,
        typical_beam_m=32,
        typical_draft_m=12.0,
    ),
    VesselClass(
        name="Panamax",
        min_dwt=65_000,
        max_dwt=99_999,
        typical_loa_m=230,
        typical_beam_m=32,
        typical_draft_m=13.5,
    ),
    VesselClass(
        name="Capesize",
        min_dwt=100_000,
        max_dwt=250_000,
        typical_loa_m=290,
        typical_beam_m=45,
        typical_draft_m=17.0,
    ),
]


def get_port_berth_records(
    ports_df,
    port_name: str,
    verified_only: bool = False,
):
    """
    Return complete berth records for a port.
    """

    result = ports_df[
        ports_df["port"].str.lower()
        == port_name.strip().lower()
    ].copy()

    if verified_only:
        result = result[
            result["data_status"].str.upper()
            == "VERIFIED"
        ]

    return result.to_dict("records")


def check_vessel_against_berth(
    vessel: VesselClass,
    berth: dict,
    operation_name: str,
) -> List[str]:
    """
    Check vessel dimensions against berth limits.
    Missing berth limits are ignored rather than guessed.
    """

    reasons = []

    max_loa = berth.get("max_loa_m")
    max_beam = berth.get("max_beam_m")
    max_draft = berth.get("max_draft_m")
    max_dwt = berth.get("max_dwt_mt")

    if max_loa is not None:

        if vessel.typical_loa_m > float(max_loa):

            reasons.append(
                f"{operation_name}: "
                f"LOA {vessel.typical_loa_m}m "
                f"exceeds berth limit {max_loa}m"
            )

    if max_beam is not None:

        if vessel.typical_beam_m > float(max_beam):

            reasons.append(
                f"{operation_name}: "
                f"Beam {vessel.typical_beam_m}m "
                f"exceeds berth limit {max_beam}m"
            )

    if max_draft is not None:

        if vessel.typical_draft_m > float(max_draft):

            reasons.append(
                f"{operation_name}: "
                f"Draft {vessel.typical_draft_m}m "
                f"exceeds berth limit {max_draft}m"
            )

    if max_dwt is not None:

        if vessel.max_dwt > float(max_dwt):

            reasons.append(
                f"{operation_name}: "
                f"DWT {vessel.max_dwt} MT "
                f"exceeds berth limit {max_dwt} MT"
            )

    return reasons


def find_feasible_berths(
    vessel: VesselClass,
    ports_df,
    port_name: str,
    operation_name: str,
    verified_only: bool = False,
):
    """
    Find all feasible berths for a vessel.
    """

    berths = get_port_berth_records(
        ports_df=ports_df,
        port_name=port_name,
        verified_only=verified_only,
    )

    feasible = []

    for berth in berths:

        reasons = check_vessel_against_berth(
            vessel=vessel,
            berth=berth,
            operation_name=operation_name,
        )

        if not reasons:
            feasible.append(berth)

    return feasible


def get_best_handling_rate(
    berths: list,
) -> Optional[float]:
    """
    Return the highest valid handling rate.
    """

    rates = []

    for berth in berths:

        rate = berth.get(
            "handling_rate_mt_day"
        )

        if rate is None:
            continue

        try:

            rate = float(rate)

            if rate > 0:
                rates.append(rate)

        except (TypeError, ValueError):
            continue

    if not rates:
        return None

    return max(rates)


def optimize_vessel(
    cargo_quantity_mt: float,
    origin_port: str,
    destination_port: str,
    sailing_days: float = 3.0,
    verified_only: bool = False,
) -> dict:
    """
    Cost-based vessel optimization with port congestion.

    Steps:

        1. Check cargo capacity.
        2. Check loading berth constraints.
        3. Check discharge berth constraints.
        4. Load congestion information.
        5. Calculate handling time.
        6. Calculate queue/idle time.
        7. Calculate vessel-time cost.
        8. Calculate total voyage-time cost.
        9. Return all feasible candidates.

    Queue time now comes from port_congestion.py.

    If no real congestion dataset exists, that module
    uses its explicitly labelled prototype fallback.
    """

    if cargo_quantity_mt <= 0:
        raise ValueError(
            "cargo_quantity_mt must be greater than 0"
        )

    if not origin_port.strip():
        raise ValueError(
            "origin_port is required"
        )

    if not destination_port.strip():
        raise ValueError(
            "destination_port is required"
        )

    if sailing_days < 0:
        raise ValueError(
            "sailing_days cannot be negative"
        )

    # ------------------------------------------------------
    # Load port database
    # ------------------------------------------------------

    ports_df = load_ports()

    # ------------------------------------------------------
    # Get congestion for route
    # ------------------------------------------------------

    congestion = calculate_route_congestion(
        origin_port=origin_port,
        destination_port=destination_port,
    )

    loading_queue_days = congestion[
        "loading"
    ][
        "queue_days"
    ]

    discharge_queue_days = congestion[
        "discharge"
    ][
        "queue_days"
    ]

    congestion_risk = congestion_risk_level(
        congestion["total_queue_days"]
    )

    candidates = []

    # ------------------------------------------------------
    # Evaluate every vessel class
    # ------------------------------------------------------

    for vessel in VESSEL_CLASSES:

        # ==================================================
        # Cargo capacity
        # ==================================================

        if cargo_quantity_mt > vessel.max_dwt:

            candidates.append(
                {
                    "vessel_type": vessel.name,
                    "feasible": False,
                    "reason": (
                        "Insufficient cargo capacity"
                    ),
                }
            )

            continue

        # ==================================================
        # Loading berth
        # ==================================================

        loading_berths = find_feasible_berths(
            vessel=vessel,
            ports_df=ports_df,
            port_name=origin_port,
            operation_name="Loading port",
            verified_only=verified_only,
        )

        # ==================================================
        # Discharge berth
        # ==================================================

        discharge_berths = find_feasible_berths(
            vessel=vessel,
            ports_df=ports_df,
            port_name=destination_port,
            operation_name="Discharge port",
            verified_only=verified_only,
        )

        reasons = []

        if not loading_berths:

            reasons.append(
                f"No feasible loading berth found "
                f"at {origin_port}"
            )

        if not discharge_berths:

            reasons.append(
                f"No feasible discharge berth found "
                f"at {destination_port}"
            )

        candidate = {
            "vessel_type": vessel.name,
            "dwt": vessel.max_dwt,
            "feasible": len(reasons) == 0,
            "reasons": reasons,
            "loading_berths": [
                berth["berth"]
                for berth in loading_berths
            ],
            "discharge_berths": [
                berth["berth"]
                for berth in discharge_berths
            ],
        }

        # ==================================================
        # Congestion data
        # ==================================================

        candidate[
            "congestion"
        ] = {
            "loading_queue_days": (
                loading_queue_days
            ),
            "discharge_queue_days": (
                discharge_queue_days
            ),
            "total_queue_days": (
                congestion["total_queue_days"]
            ),
            "risk_level": congestion_risk,
            "real_data_used": (
                congestion["real_data_used"]
            ),
            "loading_source": (
                congestion["loading"]["source"]
            ),
            "discharge_source": (
                congestion["discharge"]["source"]
            ),
        }

        # ==================================================
        # Port handling + vessel economics
        # ==================================================

        if len(reasons) == 0:

            loading_rate = get_best_handling_rate(
                loading_berths
            )

            discharge_rate = get_best_handling_rate(
                discharge_berths
            )

            candidate[
                "loading_rate_mt_day"
            ] = loading_rate

            candidate[
                "discharge_rate_mt_day"
            ] = discharge_rate

            if (
                loading_rate is not None
                and discharge_rate is not None
            ):

                # ------------------------------------------
                # Handling + queue time
                # ------------------------------------------

                port_time = (
                    calculate_total_port_time(
                        cargo_quantity_mt=(
                            cargo_quantity_mt
                        ),
                        loading_rate_mt_day=(
                            loading_rate
                        ),
                        discharge_rate_mt_day=(
                            discharge_rate
                        ),
                        loading_queue_days=(
                            loading_queue_days
                        ),
                        discharge_queue_days=(
                            discharge_queue_days
                        ),
                    )
                )

                candidate.update(
                    port_time
                )

                # ------------------------------------------
                # Vessel-time cost
                # ------------------------------------------

                vessel_cost = (
                    calculate_total_vessel_time_cost(
                        vessel_type=vessel.name,
                        sailing_days=sailing_days,
                        total_port_time_days=(
                            port_time[
                                "total_port_time_days"
                            ]
                        ),
                    )
                )

                candidate.update(
                    vessel_cost
                )

            else:

                candidate[
                    "port_time_status"
                ] = "Handling rate unavailable"

        candidates.append(candidate)

    # ------------------------------------------------------
    # Return
    # ------------------------------------------------------

    return {
        "cargo_quantity_mt": (
            cargo_quantity_mt
        ),

        "origin_port": (
            origin_port
        ),

        "destination_port": (
            destination_port
        ),

        "sailing_days": (
            sailing_days
        ),

        "congestion": congestion,

        "congestion_risk": congestion_risk,

        "recommended_vessel": None,

        "recommended_cost_usd": None,

        "candidates": candidates,
    }


if __name__ == "__main__":

    result = optimize_vessel(
        cargo_quantity_mt=60_000,
        origin_port="Paradip",
        destination_port="Visakhapatnam",
        sailing_days=3.0,
        verified_only=False,
    )

    print()
    print("=" * 75)
    print("VESSEL OPTIMIZATION")
    print("=" * 75)

    print(
        f"Cargo: "
        f"{result['cargo_quantity_mt']:,} MT"
    )

    print(
        f"Route: "
        f"{result['origin_port']} -> "
        f"{result['destination_port']}"
    )

    print(
        f"Sailing days: "
        f"{result['sailing_days']}"
    )

    print("\nCONGESTION")
    print("-" * 75)

    congestion = result["congestion"]

    print(
        f"Loading queue: "
        f"{congestion['loading']['queue_days']} days"
    )

    print(
        f"Discharge queue: "
        f"{congestion['discharge']['queue_days']} days"
    )

    print(
        f"Total queue: "
        f"{congestion['total_queue_days']} days"
    )

    print(
        f"Risk level: "
        f"{result['congestion_risk']}"
    )

    print(
        f"Real data used: "
        f"{congestion['real_data_used']}"
    )

    print("\nVESSEL CANDIDATES")
    print("-" * 75)

    for candidate in result["candidates"]:

        print(
            f"\n{candidate['vessel_type']}"
        )

        print(
            f"Feasible: "
            f"{candidate['feasible']}"
        )

        if candidate.get("reason"):
            print(
                f"Reason: "
                f"{candidate['reason']}"
            )

        if candidate.get("reasons"):
            print(
                f"Reasons: "
                f"{candidate['reasons']}"
            )

        if candidate.get("estimated_vessel_time_cost_usd"):

            print(
                f"Vessel time cost: "
                f"${candidate['estimated_vessel_time_cost_usd']:,.2f}"
            )

            print(
                f"Total vessel time: "
                f"{candidate['total_vessel_time_days']:.2f} days"
            )

            print(
                f"Total port time: "
                f"{candidate['total_port_time_days']:.2f} days"
            )

        if candidate.get("congestion"):

            print(
                f"Congestion risk: "
                f"{candidate['congestion']['risk_level']}"
            )

    print()
    print("=" * 75)
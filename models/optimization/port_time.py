from math import ceil


def calculate_handling_days(
    cargo_quantity_mt: float,
    handling_rate_mt_day: float,
) -> float:
    """
    Estimate cargo handling time in days.

    Formula:
        handling_days = cargo_quantity / handling_rate
    """

    if cargo_quantity_mt <= 0:
        raise ValueError("cargo_quantity_mt must be greater than 0")

    if handling_rate_mt_day <= 0:
        raise ValueError("handling_rate_mt_day must be greater than 0")

    return cargo_quantity_mt / handling_rate_mt_day


def calculate_port_operation_time(
    cargo_quantity_mt: float,
    loading_rate_mt_day: float,
    discharge_rate_mt_day: float,
) -> dict:
    """
    Calculate loading, discharge and total cargo-handling time.
    """

    loading_days = calculate_handling_days(
        cargo_quantity_mt,
        loading_rate_mt_day,
    )

    discharge_days = calculate_handling_days(
        cargo_quantity_mt,
        discharge_rate_mt_day,
    )

    total_handling_days = loading_days + discharge_days

    return {
        "loading_days": round(loading_days, 2),
        "discharge_days": round(discharge_days, 2),
        "total_handling_days": round(total_handling_days, 2),
    }


def estimate_idle_days(
    loading_queue_days: float = 0.0,
    discharge_queue_days: float = 0.0,
) -> dict:
    """
    Estimate waiting/idle time at the two ports.

    Queue values are scenario inputs for now.
    They will later come from congestion data.
    """

    if loading_queue_days < 0:
        raise ValueError("loading_queue_days cannot be negative")

    if discharge_queue_days < 0:
        raise ValueError("discharge_queue_days cannot be negative")

    total_idle_days = loading_queue_days + discharge_queue_days

    return {
        "loading_idle_days": round(loading_queue_days, 2),
        "discharge_idle_days": round(discharge_queue_days, 2),
        "total_idle_days": round(total_idle_days, 2),
    }


def calculate_total_port_time(
    cargo_quantity_mt: float,
    loading_rate_mt_day: float,
    discharge_rate_mt_day: float,
    loading_queue_days: float = 0.0,
    discharge_queue_days: float = 0.0,
) -> dict:
    """
    Combine handling time and idle time.
    """

    handling = calculate_port_operation_time(
        cargo_quantity_mt=cargo_quantity_mt,
        loading_rate_mt_day=loading_rate_mt_day,
        discharge_rate_mt_day=discharge_rate_mt_day,
    )

    idle = estimate_idle_days(
        loading_queue_days=loading_queue_days,
        discharge_queue_days=discharge_queue_days,
    )

    total_time = (
        handling["total_handling_days"]
        + idle["total_idle_days"]
    )

    return {
        **handling,
        **idle,
        "total_port_time_days": round(total_time, 2),
    }


if __name__ == "__main__":

    result = calculate_total_port_time(
        cargo_quantity_mt=60_000,
        loading_rate_mt_day=48_000,
        discharge_rate_mt_day=50_000,
        loading_queue_days=1.0,
        discharge_queue_days=1.5,
    )

    print("\nPort Time Calculation:")
    print(result)
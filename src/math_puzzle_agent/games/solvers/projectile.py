"""Exact Python replay of the PhysicsForge projectile screen-space physics."""

from __future__ import annotations

import math
from typing import NamedTuple

from ..schemas import PointV1, ProjectileTargetSpecV1


class ProjectileSolverResult(NamedTuple):
    winnable: bool
    closest_distance: float
    closest_point: PointV1
    closest_step: int


def simulate_projectile(
    spec: ProjectileTargetSpecV1,
    *,
    angle: int | None = None,
    power: int | None = None,
) -> ProjectileSolverResult:
    """Replay a launch and report its closest approach to the target.

    Optional controls let the API verify player attempts with the identical
    physics used to certify the stored solution.
    """

    launch_angle = spec.solution.angle if angle is None else angle
    launch_power = spec.solution.power if power is None else power
    if not spec.controls.angle.min <= launch_angle <= spec.controls.angle.max:
        raise ValueError("angle is outside the supported control range")
    if not spec.controls.thrust.min <= launch_power <= spec.controls.thrust.max:
        raise ValueError("power is outside the supported control range")

    physics = spec.physics
    radians = math.radians(launch_angle)
    speed = launch_power * physics.thrust_scale
    closest_distance = math.inf
    closest_point = PointV1(x=physics.launch_point.x, y=physics.launch_point.y)
    closest_step = 0

    for step in range(physics.max_steps):
        time = step * physics.timestep_seconds
        point = PointV1(
            x=physics.launch_point.x + speed * math.cos(radians) * time,
            y=physics.launch_point.y
            - (
                speed * math.sin(radians) * time
                - 0.5 * physics.gravity * 10 * time * time
            ),
        )
        distance = math.hypot(point.x - physics.target_x, point.y - physics.target_y)
        if distance < closest_distance:
            closest_distance = distance
            closest_point = point
            closest_step = step
        if point.x > 820 or point.y > 450:
            break

    return ProjectileSolverResult(
        winnable=closest_distance <= physics.target_tolerance,
        closest_distance=closest_distance,
        closest_point=closest_point,
        closest_step=closest_step,
    )

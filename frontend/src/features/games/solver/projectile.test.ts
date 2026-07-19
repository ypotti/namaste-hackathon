import { describe, expect, it } from "vitest";
import { projectileGameFixture } from "../fixture";
import { simulate } from "./projectile";
describe("projectile solver contract",()=>{it("proves the fixture solution is winnable",()=>{expect(simulate(projectileGameFixture,projectileGameFixture.solution.angle,projectileGameFixture.solution.power).hit).toBe(true)});it("rejects a substantially underpowered launch",()=>{expect(simulate(projectileGameFixture,20,55).hit).toBe(false)})});

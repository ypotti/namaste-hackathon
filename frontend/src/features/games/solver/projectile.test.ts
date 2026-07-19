import { describe, expect, it } from "vitest";
import { projectileFixture } from "../fixture";
import { simulate } from "./projectile";
describe("projectile solver contract",()=>{it("proves the fixture solution is winnable",()=>{expect(simulate(projectileFixture,projectileFixture.solution.angle,projectileFixture.solution.power).hit).toBe(true)});it("rejects a substantially underpowered launch",()=>{expect(simulate(projectileFixture,20,55).hit).toBe(false)})});

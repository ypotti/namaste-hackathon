import {cleanup,render,screen} from "@testing-library/react";
import {afterEach,describe,expect,it} from "vitest";
import {projectileGameFixture} from "./fixture";
import {balance,falling,fraction,graph,momentum} from "./solver/mechanics.test";
import {GameRenderer} from "./GameRenderer";
afterEach(cleanup);
describe("GameRenderer registry",()=>{
 it.each([[projectileGameFixture,"Projectile launch challenge"],[falling,"Falling object tower"],[balance,"Torque balance beam"],[momentum,"Momentum collision track"],[fraction,"Select 2/3 of 12 items"],[graph,"Linear graph matching challenge"]] as const)("dispatches $game_type",(spec,label)=>{render(<GameRenderer spec={spec as any}/>);expect(screen.getByLabelText(label)).toBeTruthy();expect(screen.getByRole("button",{name:"Check answer"})).toBeTruthy()});
 it("supports open-ended sandbox exploration",()=>{render(<GameRenderer spec={projectileGameFixture as any} mode="sandbox"/>);expect(screen.getByText("Live exploration")).toBeTruthy();expect(screen.getByRole("button",{name:"Reset variables"})).toBeTruthy();expect(screen.queryByRole("button",{name:"Check answer"})).toBeNull()});
});

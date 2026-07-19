import {cleanup,render,screen} from "@testing-library/react";
import {afterEach,describe,expect,it} from "vitest";
import {projectileFixture} from "./fixture";
import {balance,falling,fraction,graph,momentum} from "./solver/mechanics.test";
import {GameRenderer} from "./GameRenderer";
afterEach(cleanup);
describe("GameRenderer registry",()=>{it.each([[projectileFixture,"Projectile launch challenge"],[falling,"Falling object tower"],[balance,"Torque balance beam"],[momentum,"Momentum collision track"],[fraction,"Select 2/3 of 12 items"],[graph,"Linear graph matching challenge"]] as const)("dispatches $game_type",(spec,label)=>{render(<GameRenderer spec={spec}/>);expect(screen.getByLabelText(label)).toBeTruthy();expect(screen.getByRole("button",{name:"Check answer"})).toBeTruthy()})});

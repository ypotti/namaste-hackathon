import { afterEach, describe, expect, it, vi } from "vitest";
import { CONVERSATION_STORAGE_KEY, getGame, getOrCreateConversationId, getRun, runEventsUrl, submitMessage } from "./client";
import { projectileFixture } from "../features/games/fixture";

afterEach(()=>vi.unstubAllGlobals());

describe("forge API client",()=>{
  it("restores a conversation without creating another",async()=>{
    const fetchMock=vi.fn();vi.stubGlobal("fetch",fetchMock);
    const storage={getItem:vi.fn(()=>"existing-id"),setItem:vi.fn()};
    await expect(getOrCreateConversationId(storage)).resolves.toBe("existing-id");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("creates and stores a conversation when none exists",async()=>{
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>({id:"new-id",title:null,status:"active",created_at:"now"})}));
    const storage={getItem:vi.fn(()=>null),setItem:vi.fn()};
    await expect(getOrCreateConversationId(storage)).resolves.toBe("new-id");
    expect(storage.setItem).toHaveBeenCalledWith(CONVERSATION_STORAGE_KEY,"new-id");
  });

  it("posts snake_case game messages and returns the canonical game",async()=>{
    const fetchMock=vi.fn().mockResolvedValue({ok:true,json:async()=>({status:"ready",game:projectileFixture})});vi.stubGlobal("fetch",fetchMock);
    const response=await submitMessage("conversation/id","Teach projectile motion");
    expect(response.status).toBe("ready");
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/conversations/conversation%2Fid/messages",expect.objectContaining({method:"POST",body:JSON.stringify({content:"Teach projectile motion"})}));
  });

  it("encodes run and game identifiers",async()=>{
    const fetchMock=vi.fn().mockResolvedValue({ok:true,json:async()=>({id:"record",status:"processing"})});vi.stubGlobal("fetch",fetchMock);
    await getRun("run/id");
    await getGame("game/id");
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/runs/run%2Fid");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/games/game%2Fid");
    expect(runEventsUrl("run/id")).toBe("/api/v1/runs/run%2Fid/events");
  });
});

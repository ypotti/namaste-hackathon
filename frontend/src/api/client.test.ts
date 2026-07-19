import { afterEach, describe, expect, it, vi } from "vitest";
import { CONVERSATION_PARAM_KEY, getGame, getOrCreateConversationId, getRun, runEventsUrl, submitMessage, forgetConversation } from "./client";
import { projectileFixture } from "../features/games/fixture";

afterEach(()=>vi.unstubAllGlobals());

describe("forge API client",()=>{
  it("restores a conversation without creating another",async()=>{
    const fetchMock=vi.fn().mockResolvedValue({ok:true,json:async()=>({id:"existing-id"})});
    vi.stubGlobal("fetch",fetchMock);
    vi.stubGlobal("location", {
      search: "?conversation_id=existing-id",
      href: "http://localhost/?conversation_id=existing-id",
      pathname: "/"
    });
    await expect(getOrCreateConversationId()).resolves.toBe("existing-id");
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/conversations/existing-id",expect.any(Object));
  });

  it("creates and stores a conversation when none exists",async()=>{
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>({id:"new-id",title:null,status:"active",created_at:"now"})}));
    vi.stubGlobal("location", {
      search: "",
      href: "http://localhost/",
      pathname: "/"
    });
    const replaceStateMock = vi.fn();
    vi.stubGlobal("history", { replaceState: replaceStateMock });
    
    await expect(getOrCreateConversationId()).resolves.toBe("new-id");
    expect(replaceStateMock).toHaveBeenCalledWith({}, "", "/?conversation_id=new-id");
  });

  it("replaces a stale stored conversation",async()=>{
    const fetchMock=vi.fn()
      .mockResolvedValueOnce({ok:false,status:404,json:async()=>({detail:"Conversation not found"})})
      .mockResolvedValueOnce({ok:true,json:async()=>({id:"replacement-id"})});
    vi.stubGlobal("fetch",fetchMock);
    vi.stubGlobal("location", {
      search: "?conversation_id=stale-id",
      href: "http://localhost/?conversation_id=stale-id",
      pathname: "/"
    });
    const replaceStateMock = vi.fn();
    vi.stubGlobal("history", { replaceState: replaceStateMock });

    await expect(getOrCreateConversationId()).resolves.toBe("replacement-id");
    expect(replaceStateMock).toHaveBeenCalledWith({}, "", "/");
    expect(replaceStateMock).toHaveBeenCalledWith({}, "", "/?conversation_id=replacement-id");
  });

  it("clears the conversation ID from the URL",()=>{
    vi.stubGlobal("location", {
      search: "?conversation_id=some-id",
      href: "http://localhost/?conversation_id=some-id",
      pathname: "/"
    });
    const replaceStateMock = vi.fn();
    vi.stubGlobal("history", { replaceState: replaceStateMock });

    forgetConversation();
    expect(replaceStateMock).toHaveBeenCalledWith({}, "", "/");
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

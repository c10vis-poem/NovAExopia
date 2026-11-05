// UNTESTED. claw-mcp: stdio MCP server, 6 tools, driver per tool. JDK HttpClient, no OkHttp, to stay small.
// Embeddable: call Server.handle(JsonObject) from AEthX-AEsc; main() is only the stdio loop.
package claw

import kotlinx.serialization.json.*
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse

fun interface Driver { fun call(a: JsonObject): String }

object Drivers {
    private val http = HttpClient.newHttpClient()
    private val cdp = "http://127.0.0.1:" + (System.getenv("CDP_PORT") ?: "9222")
    private fun get(u: String, h: Map<String, String> = emptyMap(), body: String? = null): String {
        val b = HttpRequest.newBuilder(URI(u)).header("User-Agent", "claw-mcp/0.1")
        h.forEach { (k, v) -> b.header(k, v) }
        if (body != null) b.POST(HttpRequest.BodyPublishers.ofString(body))
        return http.send(b.build(), HttpResponse.BodyHandlers.ofString()).body()
    }
    private fun JsonObject.s(k: String) = this[k]?.jsonPrimitive?.contentOrNull

    val search = Driver { error("not-implemented: wire a search provider (Perplexity/SearXNG) here") }
    val scrape = Driver { a ->
        val n = a["max_chars"]?.jsonPrimitive?.intOrNull ?: 20000
        val raw = get(a.s("url")!!)
        if (a.s("format") == "html") raw.take(n)
        else raw.replace(Regex("(?is)<(script|style)\\b.*?</\\1>"), " ").replace(Regex("<[^>]+>"), " ")
            .replace(Regex("\\s+"), " ").trim().take(n)
    }
    // TODO: CDP websocket actions (navigate/eval/click) via java.net.http.WebSocket.
    val browser = Driver { a ->
        when (a.s("action") ?: "version") {
            "version" -> get("$cdp/json/version")
            "tabs" -> get("$cdp/json/list")
            else -> error("not-implemented: CDP websocket action")
        }
    }
    val device = Driver { a ->
        val cmd = when (a.s("action")) {
            "battery" -> listOf("termux-battery-status"); "wifi" -> listOf("termux-wifi-connectioninfo")
            "notify" -> listOf("termux-notification") + (a["args"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList())
            "adb-devices" -> listOf("adb", "devices")
            else -> error("action must be battery|wifi|notify|adb-devices")
        }
        val p = ProcessBuilder(cmd).redirectErrorStream(true).start()
        p.inputStream.bufferedReader().readText().trim()
    }
    val infer = Driver { a ->
        val key = System.getenv("OPENROUTER_API_KEY") ?: error("not-implemented: set OPENROUTER_API_KEY (Claude/Gemini/Vertex drivers TODO)")
        val body = buildJsonObject {
            put("model", a.s("model")!!)
            putJsonArray("messages") { addJsonObject { put("role", "user"); put("content", a.s("prompt")!!) } }
        }.toString()
        val r = Json.parseToJsonElement(get("https://openrouter.ai/api/v1/chat/completions",
            mapOf("Authorization" to "Bearer $key", "Content-Type" to "application/json"), body)).jsonObject
        r["choices"]!!.jsonArray[0].jsonObject["message"]!!.jsonObject["content"]!!.jsonPrimitive.content
    }
    val workflows = Driver { a ->
        val f = java.io.File(System.getenv("CLAW_WORKFLOWS") ?: "workflows.json")
        val wf = if (f.exists()) Json.parseToJsonElement(f.readText()).jsonObject else JsonObject(emptyMap())
        if ((a.s("action") ?: "list") == "list") JsonArray(wf.keys.sorted().map(::JsonPrimitive)).toString()
        else JsonArray(wf[a.s("name")!!]!!.jsonArray.map {
            val st = it.jsonObject
            JsonPrimitive(Server.tools.getValue(st.s("tool")!!).second.call(st["arguments"]?.jsonObject ?: JsonObject(emptyMap())))
        }).toString()
    }
}

object Server {
    private fun schema(vararg props: Pair<String, String>, req: List<String> = emptyList()) = buildJsonObject {
        put("type", "object")
        putJsonObject("properties") { props.forEach { (k, t) -> putJsonObject(k) { put("type", t) } } }
        putJsonArray("required") { req.forEach { add(it) } }
    }
    // name -> (description + schema, driver)
    val tools: Map<String, Pair<Pair<String, JsonObject>, Driver>> = mapOf(
        "claw.search" to (("Web search via a provider driver." to schema("query" to "string", req = listOf("query"))) to Drivers.search),
        "claw.scrape" to (("Fetch a URL; return text (or html)." to schema("url" to "string", "format" to "string", "max_chars" to "integer", req = listOf("url"))) to Drivers.scrape),
        "claw.browser" to (("Phone Chrome over CDP :9222." to schema("action" to "string")) to Drivers.browser),
        "claw.device" to (("Android/Termux device: battery|wifi|notify|adb-devices." to schema("action" to "string", "args" to "array", req = listOf("action"))) to Drivers.device),
        "claw.infer" to (("Multi-provider inference." to schema("provider" to "string", "model" to "string", "prompt" to "string", req = listOf("model", "prompt"))) to Drivers.infer),
        "claw.workflows" to (("action list|run; run needs name." to schema("action" to "string", "name" to "string")) to Drivers.workflows),
    )

    fun handle(m: JsonObject): JsonObject? {
        val id = m["id"] ?: return null
        val method = m["method"]?.jsonPrimitive?.content
        fun ok(r: JsonElement) = buildJsonObject { put("jsonrpc", "2.0"); put("id", id); put("result", r) }
        fun err(c: Int, msg: String) = buildJsonObject {
            put("jsonrpc", "2.0"); put("id", id); putJsonObject("error") { put("code", c); put("message", msg) }
        }
        return when (method) {
            "initialize" -> ok(buildJsonObject {
                put("protocolVersion", m["params"]?.jsonObject?.get("protocolVersion") ?: JsonPrimitive("2024-11-05"))
                putJsonObject("capabilities") { putJsonObject("tools") {} }
                putJsonObject("serverInfo") { put("name", "claw-mcp"); put("version", "0.1.0") }
            })
            "ping" -> ok(JsonObject(emptyMap()))
            "tools/list" -> ok(buildJsonObject {
                putJsonArray("tools") {
                    tools.forEach { (n, t) -> addJsonObject { put("name", n); put("description", t.first.first); put("inputSchema", t.first.second) } }
                }
            })
            "tools/call" -> {
                val p = m["params"]!!.jsonObject
                val t = tools[p["name"]?.jsonPrimitive?.content] ?: return err(-32602, "unknown tool")
                val (text, bad) = try { t.second.call(p["arguments"]?.jsonObject ?: JsonObject(emptyMap())) to false }
                catch (e: Exception) { "${e::class.simpleName}: ${e.message}" to true }
                ok(buildJsonObject {
                    putJsonArray("content") { addJsonObject { put("type", "text"); put("text", text) } }
                    if (bad) put("isError", true)
                })
            }
            else -> err(-32601, "method not found")
        }
    }
}

fun main(args: Array<String>) {
    // --stdio is the only transport; flag accepted for parity with the launcher.
    generateSequence(::readLine).filter { it.isNotBlank() }.forEach { line ->
        val out = try { Server.handle(Json.parseToJsonElement(line).jsonObject) } catch (e: Exception) { null }
        if (out != null) { println(out.toString()); System.out.flush() }
    }
}

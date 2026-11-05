// UNTESTED: no kotlinc/gradle on the device when written. Build with ../bin/build-kotlin.sh.
plugins {
    kotlin("jvm") version "2.0.21"
    kotlin("plugin.serialization") version "2.0.21"
    id("com.gradleup.shadow") version "8.3.5"
}
repositories { mavenCentral() }
dependencies { implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3") }
kotlin { jvmToolchain(17) }
tasks.shadowJar {
    archiveBaseName.set("claw-mcp"); archiveClassifier.set("all"); archiveVersion.set("")
    manifest { attributes["Main-Class"] = "claw.MainKt" }
}

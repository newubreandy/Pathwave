import java.util.Properties
import java.io.FileInputStream

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// PR #57 — Release signing
//   1) android/key.properties (gitignored — 로컬/CI 키스토어 경로 + 비번)
//   2) ENV: PATHWAVE_KEYSTORE / PATHWAVE_KEYSTORE_PASSWORD / PATHWAVE_KEY_ALIAS / PATHWAVE_KEY_PASSWORD
//   3) 둘 다 없으면 debug 로 fallback (개발 빌드용 — 출시 빌드는 별도 점검 필요)
val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

fun envOrProp(envKey: String, propKey: String): String? {
    return System.getenv(envKey) ?: keystoreProperties.getProperty(propKey)
}

val releaseStoreFile     = envOrProp("PATHWAVE_KEYSTORE",          "storeFile")
val releaseStorePassword = envOrProp("PATHWAVE_KEYSTORE_PASSWORD", "storePassword")
val releaseKeyAlias      = envOrProp("PATHWAVE_KEY_ALIAS",         "keyAlias")
val releaseKeyPassword   = envOrProp("PATHWAVE_KEY_PASSWORD",      "keyPassword")
val hasReleaseSigning    = listOf(releaseStoreFile, releaseStorePassword, releaseKeyAlias, releaseKeyPassword).all { !it.isNullOrEmpty() }

android {
    namespace = "com.triggersoft.pathwave"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        // 2026-06-09 — flutter_local_notifications 가 요구하는 core library desugaring 활성화.
        isCoreLibraryDesugaringEnabled = true
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.triggersoft.pathwave"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                storeFile     = file(releaseStoreFile!!)
                storePassword = releaseStorePassword
                keyAlias      = releaseKeyAlias
                keyPassword   = releaseKeyPassword
            }
        }
    }

    buildTypes {
        release {
            signingConfig = if (hasReleaseSigning) {
                signingConfigs.getByName("release")
            } else {
                logger.warn("⚠️  PathWave: release 키스토어가 설정되지 않아 debug 키로 서명합니다. 출시 빌드 전 PATHWAVE_KEYSTORE ENV 또는 android/key.properties 설정 필수.")
                signingConfigs.getByName("debug")
            }
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }
}

flutter {
    source = "../.."
}

dependencies {
    // 2026-06-09 — desugaring runtime (flutter_local_notifications 요구사항).
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
}

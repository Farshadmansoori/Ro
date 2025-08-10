plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.example.roapp"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.example.roapp"
        minSdk = 24
        targetSdk = 34
        versionCode = 2
        versionName = "0.2"

        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64", "x86") }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
        debug { isMinifyEnabled = false }
    }
    buildFeatures { compose = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.14" }
    packaging { resources.excludes += "/META-INF/{AL2.0,LGPL2.1}" }
}

chaquopy {
    defaultConfig {
        pip.install("numpy==1.26.4")
        pip.install("pandas==2.2.2")
        // matplotlib optional; comment out to shrink APK
        // pip.install("matplotlib==3.8.4")
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.06.00")
    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.1")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
}

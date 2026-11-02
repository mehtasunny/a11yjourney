plugins {
    id("com.android.application")
}

android {
    namespace = "io.github.mehtasunny.atfscan"
    compileSdk = 37

    defaultConfig {
        applicationId = "io.github.mehtasunny.atfscan"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation(
        "com.google.android.apps.common.testing.accessibility.framework:accessibility-test-framework:4.1.1",
    )
    // ATF's public API returns Guava collections but does not expose Guava to compilers
    androidTestImplementation("com.google.guava:guava:33.3.1-android")
}

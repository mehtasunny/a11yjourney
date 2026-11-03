package io.github.mehtasunny.atfscan;

import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.Instrumentation;
import android.app.UiAutomation;
import android.content.Context;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;
import android.view.accessibility.AccessibilityNodeInfo;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.apps.common.testing.accessibility.framework.AccessibilityCheckPreset;
import com.google.android.apps.common.testing.accessibility.framework.AccessibilityCheckResult.AccessibilityCheckResultType;
import com.google.android.apps.common.testing.accessibility.framework.AccessibilityHierarchyCheck;
import com.google.android.apps.common.testing.accessibility.framework.AccessibilityHierarchyCheckResult;
import com.google.android.apps.common.testing.accessibility.framework.Parameters;
import com.google.android.apps.common.testing.accessibility.framework.replacements.Rect;
import com.google.android.apps.common.testing.accessibility.framework.uielement.AccessibilityHierarchyAndroid;
import com.google.android.apps.common.testing.accessibility.framework.uielement.ViewHierarchyElement;
import com.google.android.apps.common.testing.accessibility.framework.utils.contrast.BitmapImage;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Locale;

/**
 * Runs Google's Accessibility Test Framework (the engine behind Accessibility Scanner) on
 * whatever app is in the foreground, and logs each error or warning as one JSON line under the
 * tag ATFSCAN. Used as an independent second opinion next to A11yJourney.
 */
@RunWith(AndroidJUnit4.class)
public class ScanTest {
    private static final String TAG = "ATFSCAN";

    @Test
    public void scanForegroundApp() throws Exception {
        Instrumentation inst = InstrumentationRegistry.getInstrumentation();
        UiAutomation ua = inst.getUiAutomation();
        Bundle args = InstrumentationRegistry.getArguments();
        String screen = args.getString("screen", "screen");
        // Read the same tree uiautomator reads: include views not marked important, which is
        // how Jetpack Compose exposes many of its semantics nodes.
        AccessibilityServiceInfo info = ua.getServiceInfo();
        info.flags |= AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
                | AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;
        ua.setServiceInfo(info);
        try {
            ua.waitForIdle(500, 5000);
        } catch (java.util.concurrent.TimeoutException ignored) {
            // live screens may never go fully idle; scan what is there
        }

        AccessibilityNodeInfo root = null;
        for (int i = 0; i < 20 && root == null; i++) {
            root = ua.getRootInActiveWindow();
            if (root == null) SystemClock.sleep(500);
        }
        if (root == null) {
            Log.i(TAG, new JSONObject().put("screen", screen).put("error", "no active window").toString());
            return;
        }
        Context context = inst.getContext();
        AccessibilityHierarchyAndroid hierarchy =
                AccessibilityHierarchyAndroid.newBuilder(root, context).build();
        Parameters parameters = new Parameters();
        Bitmap shot = ua.takeScreenshot();
        if (shot != null) {
            parameters.putScreenCapture(new BitmapImage(shot));
        }
        int views = hierarchy.getActiveWindow().getAllViews().size();
        Log.i(TAG, new JSONObject().put("screen", screen)
                .put("debug", "root=" + root.getPackageName() + " class=" + root.getClassName()
                        + " children=" + root.getChildCount() + " views=" + views
                        + " screenshot=" + (shot != null)).toString());
        int count = 0;
        for (AccessibilityHierarchyCheck check :
                AccessibilityCheckPreset.getAccessibilityHierarchyChecksForPreset(
                        AccessibilityCheckPreset.LATEST)) {
            for (AccessibilityHierarchyCheckResult r :
                    check.runCheckOnHierarchy(hierarchy, null, parameters)) {
                AccessibilityCheckResultType type = r.getType();
                if (type != AccessibilityCheckResultType.ERROR
                        && type != AccessibilityCheckResultType.WARNING) {
                    continue;
                }
                JSONObject o = new JSONObject()
                        .put("screen", screen)
                        .put("package", String.valueOf(root.getPackageName()))
                        .put("check", check.getClass().getSimpleName())
                        .put("type", type.name())
                        .put("message", String.valueOf(r.getMessage(Locale.ENGLISH)));
                ViewHierarchyElement e = r.getElement();
                if (e != null) {
                    Rect b = e.getBoundsInScreen();
                    o.put("bounds", new JSONArray()
                            .put(b.getLeft()).put(b.getTop()).put(b.getRight()).put(b.getBottom()));
                    o.put("class", String.valueOf(e.getClassName()));
                    o.put("resource", String.valueOf(e.getResourceName()));
                    o.put("text", String.valueOf(e.getText()));
                    o.put("desc", String.valueOf(e.getContentDescription()));
                }
                Log.i(TAG, o.toString());
                count++;
            }
        }
        Log.i(TAG, new JSONObject().put("screen", screen).put("summary", count).toString());
    }
}

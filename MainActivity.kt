package com.example.roapp

import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.documentfile.provider.DocumentFile
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))
        setContent { AppScreen() }
    }
}

@Composable
fun AppScreen() {
    var status by remember { mutableStateOf("Ready") }
    var summary by remember { mutableStateOf<String?>(null) }
    val ctx = androidx.compose.ui.platform.LocalContext.current

    val pickCsv = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument(),
        onResult = { uri: Uri? ->
            if (uri != null) {
                status = "Reading CSV..."
                val text = readTextFromUri(ctx, uri)
                if (text != null) {
                    status = "Processing in Python..."
                    val py = Python.getInstance()
                    val mod = py.getModule("ro_core")
                    val result = mod.callAttr("process_csv_text", text).toString()
                    summary = result
                    status = "Done"
                } else {
                    status = "Failed to read CSV"
                }
            }
        }
    )

    Scaffold(
        topBar = { SmallTopAppBar(title = { Text("RO Normalizer v0.2") }) }
    ) { pads ->
        Column(Modifier.padding(pads).padding(16.dp)) {
            Text("وارد کردن CSV و نرمال‌سازی آفلاین", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(12.dp))
            Button(onClick = {
                pickCsv.launch(arrayOf("text/csv", "text/comma-separated-values", "application/vnd.ms-excel"))
            }) { Text("انتخاب فایل CSV") }
            Spacer(Modifier.height(12.dp))
            Text("وضعیت: " + status)
            Spacer(Modifier.height(12.dp))
            if (summary != null) {
                Text("خلاصه نتایج:", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(8.dp))
                Text(summary!!)
            }
        }
    }
}

@Composable
fun readTextFromUri(ctx: android.content.Context, uri: Uri): String? {
    return try {
        ctx.contentResolver.takePersistableUriPermission(uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
        ctx.contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
    } catch (e: Exception) {
        null
    }
}

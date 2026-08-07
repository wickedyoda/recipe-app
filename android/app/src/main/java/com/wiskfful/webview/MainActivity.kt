package com.wiskfful.webview

import android.annotation.SuppressLint
import android.content.Context
import android.os.Bundle
import android.view.View
import android.view.inputmethod.EditorInfo
import android.webkit.WebChromeClient
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowInsetsControllerCompat

private const val PREFS_NAME = "host_prefs"
private const val KEY_HOST = "host_name"

class MainActivity : AppCompatActivity() {
    private lateinit var urlInput: EditText
    private lateinit var connectBtn: Button

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = android.graphics.Color.parseColor("#0f1115")
        WindowInsetsControllerCompat(window, window.decorView).isAppearanceLightContent = false

        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val savedHost = prefs.getString(KEY_HOST, "").orEmpty()

        if (savedHost.isNotEmpty()) {
            launchWebView(savedHost)
        } else {
            setContentView(R.layout.activity_main)
            urlInput = findViewById(R.id.urlInput)
            connectBtn = findViewById(R.id.connectBtn)

            urlInput.imeOptions = EditorInfo.IME_ACTION_GO
            urlInput.setOnEditorActionListener { _, actionId, _ ->
                if (actionId == EditorInfo.IME_ACTION_GO) {
                    onConnectClicked()
                    true
                } else false
            }

            connectBtn.setOnClickListener { onConnectClicked() }
        }
    }

    private fun onConnectClicked() {
        val host = urlInput.text.toString().trim()
        if (host.isEmpty()) {
            Toast.makeText(this, "Enter server URL", Toast.LENGTH_SHORT).show()
            return
        }
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_HOST, host).apply()
        launchWebView(host)
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun launchWebView(host: String) {
        val webView = android.webkit.WebView(this)
        setContentView(webView)

        val url = if (host.startsWith("http")) host else "http://$host"
        val ws = webView.settings
        ws.javaScriptEnabled = true
        ws.domStorageEnabled = true
        ws.loadWithOverviewMode = true
        ws.useWideViewPort = true
        ws.allowFileAccess = true
        ws.allowContentAccess = true
        webView.webChromeClient = WebChromeClient()
        webView.loadUrl(url)
    }
}

package com.cookierue.webview

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebChromeClient
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.cookierue.webview.databinding.ActivityMainBinding

private const val PREFS_NAME = "host_prefs"
private const val KEY_HOST = "host_name"

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
        val savedHost = prefs.getString(KEY_HOST, "").orEmpty()

        if (savedHost.isEmpty()) {
            showHostDialog(prefs)
        } else {
            setupWebView(savedHost)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView(host: String) {
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val url = if (host.startsWith("http")) host else "http://$host"
        val ws = binding.webView.settings
        ws.javaScriptEnabled = true
        ws.domStorageEnabled = true
        ws.loadWithOverviewMode = true
        ws.useWideViewPort = true
        binding.webView.webChromeClient = WebChromeClient()
        binding.webView.loadUrl(url)
    }

    private fun showHostDialog(prefs: android.content.SharedPreferences) {
        val input = EditText(this).apply {
            hint = "Enter website address (e.g. 192.168.1.100:3000)"
            setText(prefs.getString(KEY_HOST, ""))
        }

        AlertDialog.Builder(this)
            .setTitle("Enter Host Name")
            .setView(input)
            .setPositiveButton("Save") { _, _ ->
                val host = input.text.toString().trim()
                if (host.isNotEmpty()) {
                    prefs.edit().putString(KEY_HOST, host).apply()
                    setupWebView(host)
                    Toast.makeText(this, "Host saved: $host", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this, "Host required", Toast.LENGTH_SHORT).show()
                    showHostDialog(prefs)
                }
            }
            .setNegativeButton("Cancel") { _, _ ->
                val savedHost = prefs.getString(KEY_HOST, "").orEmpty()
                if (savedHost.isNotEmpty()) {
                    setupWebView(savedHost)
                } else {
                    finish()
                }
            }
            .create()
            .show()
    }

    override fun onBackPressed() {
        if (::binding.isInitialized && binding.webView.canGoBack()) {
            binding.webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}

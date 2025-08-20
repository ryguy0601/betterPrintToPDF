using System.Text.Json;
using System.Text.Json.Serialization;
using System.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Concurrent;

namespace WebApplication1.wwwroot.Helpers
{
    public class SiteInfo
    {
        [JsonPropertyName("s")]
        public string stage { get; set; } = string.Empty; // stage URL
        [JsonPropertyName("p")]
        public string prod { get; set; } = string.Empty; // prod URL
    }
    public class RunPython : Controller
    {
        private readonly string pythonPath = "C:\\Users\\ryguy\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe";

        public Dictionary<string, SiteInfo> getJson()
        {
            string SitesJson = "[]";
            string scriptPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "python", "getJson.py");

            var psi = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = $"\"{scriptPath}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = false
            };

            using var process = Process.Start(psi);
            if (process == null)
            {
                SitesJson = "Error: Failed to start Python process.";
                return new Dictionary<string, SiteInfo>();
            }
            string output = process.StandardOutput.ReadToEnd();
            string errors = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                // Handle Python errors
                SitesJson = $"Error: {errors}";
                return new Dictionary<string, SiteInfo>();
            }

            // Store JSON string for debugging or displaying
            SitesJson = output;

            // Deserialize JSON into Sites dictionary
            return JsonSerializer.Deserialize<Dictionary<string, SiteInfo>>(output)
                    ?? new Dictionary<string, SiteInfo>();
        }

        //public IActionResult runMain(string JobId, string site, string siteURL, string env, string res)
        //{

        //    string scriptPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "python", "main.py");

        //    var psi = new ProcessStartInfo
        //    {
        //        FileName = pythonPath,
        //        Arguments = $"\"{scriptPath}\" \"{JobId}\" \"{site}\" \"{siteURL}\" \"{env}\" \"{res}\" ",
        //        RedirectStandardOutput = true,
        //        RedirectStandardError = true,
        //        UseShellExecute = false,
        //        CreateNoWindow = true
        //    };
        //    //var psi = new ProcessStartInfo
        //    //{
        //    //    FileName = "cmd.exe",
        //    //    Arguments = $"/k \"{pythonPath}\" \"{scriptPath}\" \"{JobId}\" \"{site}\" \"{siteURL}\" \"{env}\" \"{res}\" ", // /k keeps window open, /c closes it after running
        //    //    UseShellExecute = true,  // Must be true to show a window
        //    //    CreateNoWindow = false
        //    //};

        //    using var process = Process.Start(psi);
        //    Console.WriteLine(JobId);
        //    return RedirectToPage("/preview", new { jobId = JobId });
        //}

        public IActionResult runMain(string JobId, string site, string siteURL, string env, string res, string username, string password)
        {
            string scriptPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "python", "main.py");

            string args = $"\"{scriptPath}\" \"{JobId}\" \"{site}\" \"{siteURL}\" \"{env}\" \"{res}\" \"{username}\" \"{password}\" ";
            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
            {
                args = $"\"{scriptPath}\" \"{JobId}\" \"{site}\" \"{siteURL}\" \"{env}\" \"{res}\" ";
            }

            //Path for log file

            string logDir = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "logs");
            Directory.CreateDirectory(logDir); // make sure it exists
            string logFile = Path.Combine(logDir, $"{JobId}.log");

            var psi = new ProcessStartInfo
            {
                FileName = pythonPath, // full path to python.exe
                Arguments = args,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            //Run in background so web request doesn’t block


            Task.Run(() =>
            {
                using var process = new Process { StartInfo = psi };
                using var logStream = new StreamWriter(logFile, append: true) { AutoFlush = true };

                process.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                        logStream.WriteLine($"[OUT] {e.Data}");
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                        logStream.WriteLine($"[ERR] {e.Data}");
                };

                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                process.WaitForExit();
            });

            return RedirectToPage("/preview", new { jobId = JobId });
        }
    }

    public class PythonExecutionService : BackgroundService
    {
        private readonly ConcurrentQueue<(string JobId, string Site, string SiteURL, string Env, string Res)> _taskQueue = new();

        public void EnqueueTask(string jobId, string site, string siteURL, string env, string res)
        {
            _taskQueue.Enqueue((jobId, site, siteURL, env, res));
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                if (_taskQueue.TryDequeue(out var task))
                {
                    //Execute Python script
                   var psi = new ProcessStartInfo
                   {
                       FileName = "python",
                       Arguments = $"\"main.py\" \"{task.JobId}\" \"{task.Site}\" \"{task.SiteURL}\" \"{task.Env}\" \"{task.Res}\"",
                       RedirectStandardOutput = true,
                       RedirectStandardError = true,
                       UseShellExecute = false,
                       CreateNoWindow = true
                   };

                    using var process = Process.Start(psi);
                    if (process != null)
                    {
                        string output = await process.StandardOutput.ReadToEndAsync();
                        string errors = await process.StandardError.ReadToEndAsync();
                        process.WaitForExit();

                        //Log output and errors
                            Console.WriteLine(output);
                        Console.WriteLine(errors);
                    }
                }

                await Task.Delay(1000, stoppingToken); // Polling interval
            }
        }
    }
}

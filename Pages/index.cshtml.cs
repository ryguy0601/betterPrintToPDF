using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using WebApplication1.wwwroot.Helpers;

namespace WebApplication1.Pages
{
    public class RunPythonModel : PageModel
    {
        private readonly RunPython _runPython;

        public RunPythonModel(RunPython runPython)
        {
            _runPython = runPython;
        }

        public Dictionary<string, SiteInfo> Sites { get; set; } = new();

        [BindProperty]
        public string site { get; set; } = "";

        [BindProperty]
        public string res { get; set; } = "";

        [BindProperty]
        public string env { get; set; } = "";

        [BindProperty]
        public string customSite { get; set; } = "";

        [BindProperty]
        public string username { get; set; } = "";

        [BindProperty]
        public string password { get; set; } = "";

        public void OnGet()
        {
            Sites = _runPython.getJson();
        }

        public IActionResult OnPost()
        {
            Sites = _runPython.getJson();

            string siteURL;

            if (site.Contains("other"))
            {
                siteURL = customSite;
            }
            else if (env.Contains("prod"))
            {
                siteURL = Sites[site].prod;
            }
            else
            {
                siteURL = Sites[site].stage;
            }

            return _runPython.runMain(Guid.NewGuid().ToString(), site, siteURL, env, res, username, password);
        }
    }
}
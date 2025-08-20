using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using WebApplication1.wwwroot.Helpers;


namespace WebApplication1.Pages
{
    public class PreviewModel : PageModel
    {
        public Dictionary<string, SiteInfo> Sites { get; set; } = new();

        [BindProperty]
        public string Site { get; set; } = "";

        [BindProperty]
        public string Res { get; set; } = "";

        [BindProperty]
        public string Env { get; set; } = "";

        [BindProperty]
        public string CustomSite { get; set; } = "";
        
        [BindProperty]
        public string username { get; set; } = "";

        [BindProperty]
        public string password { get; set; } = "";

        public RunPython runPython = new();
        public void OnGet()
        {

            Sites = runPython.getJson();

        }

        public IActionResult OnPost()
        {
            Sites = runPython.getJson();

            string siteURL;

            if (Site.Contains("other"))
            {
                siteURL = CustomSite;
            }
            else if (Env.Contains("prod"))
            {
                siteURL = Sites[Site].prod;
            }
            else
            {
                siteURL = Sites[Site].stage;
            }
            return runPython.runMain(Guid.NewGuid().ToString(), Site, siteURL, Env, Res, username, password);
        }



    }
}

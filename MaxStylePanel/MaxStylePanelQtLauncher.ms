macroScript MaxStylePanelQtLauncher
category:"StyleTools"
toolTip:"Max Style Panel (Qt)"
(
    on execute do
    (
        python.ExecuteFile (getFilenamePath (getSourceFileName()) + "MaxStylePanelQt.py")
    )
) 
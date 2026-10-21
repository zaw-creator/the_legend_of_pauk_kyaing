using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Presets;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace PaukKyaing.EditorTools
{
    /// <summary>
    /// One-time setup of the project for pixel art: the game is drawn at 480x270 with 16 pixels per unit and shown
    /// at 4x on a 1080p screen (see the GDD, Rendering). Safe to run again: it only sets values and rebuilds the
    /// look-test scene. Menu: Tools > Pauk Kyaing > Set Up Pixel Project.
    /// </summary>
    public static class PixelProjectSetup
    {
        public const int PixelsPerUnit = 16;
        public const int RefWidth = 480;
        public const int RefHeight = 270;

        const string ArtRoot = "Assets/Art";
        const string PresetPath = "Assets/Settings/Presets/PixelSprite.preset";
        const string LookTestArt = "Assets/Art/LookTest";
        const string LookTestScene = "Assets/Scenes/LookTest.unity";

        static readonly string[] Folders =
        {
            "Assets/Art/Characters", "Assets/Art/Environments", "Assets/Art/UI", "Assets/Art/LookTest",
            "Assets/Audio/Music", "Assets/Audio/SFX", "Assets/Data", "Assets/Localization", "Assets/Prefabs",
            "Assets/Scenes", "Assets/Scripts/Runtime", "Assets/Scripts/Editor", "Assets/Settings/Presets",
        };

        // Menu layers baked to the 480x270 grid, back to front. All are full-frame images centred on the camera.
        static readonly (string file, int order)[] LookTestLayers =
        {
            ("lt_far", 0), ("lt_naga_back", 10), ("lt_palace", 20), ("lt_naga_front", 30), ("lt_wall", 40),
            ("lt_hero", 50), ("lt_tree_r", 60), ("lt_tree_l", 61),
        };

        [MenuItem("Tools/Pauk Kyaing/Set Up Pixel Project")]
        public static void Run()
        {
            MakeFolders();
            PlayerAndQuality();
            PixelSpritePreset();
            UrpForPixels();
            BuildLookTestScene();
            AssetDatabase.SaveAssets();
            Debug.Log("[PixelProjectSetup] Done.");
        }

        /// <summary>Batch mode: set up, then render the look-test scene to the PNG named by -renderOut.</summary>
        public static void RunBatch()
        {
            Run();
            var args = Environment.GetCommandLineArgs();
            var i = Array.IndexOf(args, "-renderOut");
            if (i >= 0 && i + 1 < args.Length)
                RenderLookTest(args[i + 1]);
        }

        static void MakeFolders()
        {
            foreach (var folder in Folders)
            {
                if (AssetDatabase.IsValidFolder(folder))
                    continue;
                var parent = Path.GetDirectoryName(folder).Replace('\\', '/');
                foreach (var part in parent.Split('/').Skip(1).Select((_, k) => string.Join("/", parent.Split('/').Take(k + 2))))
                    if (!AssetDatabase.IsValidFolder(part))
                        AssetDatabase.CreateFolder(Path.GetDirectoryName(part).Replace('\\', '/'), Path.GetFileName(part));
                AssetDatabase.CreateFolder(parent, Path.GetFileName(folder));
            }
        }

        static void PlayerAndQuality()
        {
            PlayerSettings.companyName = "zaw-creator";
            PlayerSettings.productName = "The Legend of Maung Pauk Kyaing";
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.fullScreenMode = FullScreenMode.FullScreenWindow;
            PlayerSettings.resizableWindow = true;

            // no texture smoothing or edge blending anywhere: it would blur the pixel grid
            var current = QualitySettings.GetQualityLevel();
            for (var level = 0; level < QualitySettings.names.Length; level++)
            {
                QualitySettings.SetQualityLevel(level, false);
                QualitySettings.anisotropicFiltering = AnisotropicFiltering.Disable;
                QualitySettings.antiAliasing = 0;
                QualitySettings.globalTextureMipmapLimit = 0;
            }
            QualitySettings.SetQualityLevel(current, false);
        }

        /// <summary>Every texture under Assets/Art imports as a crisp pixel sprite: point filter, no compression,
        /// no mipmaps, 16 pixels per unit.</summary>
        static void PixelSpritePreset()
        {
            var sample = AssetDatabase.FindAssets("t:Texture2D", new[] { ArtRoot })
                .Select(AssetDatabase.GUIDToAssetPath).FirstOrDefault();
            if (sample == null)
            {
                Debug.LogWarning("[PixelProjectSetup] No texture under Assets/Art to build the preset from.");
                return;
            }
            var importer = (TextureImporter)AssetImporter.GetAtPath(sample);
            ConfigurePixelSprite(importer);

            var preset = AssetDatabase.LoadAssetAtPath<Preset>(PresetPath);
            if (preset == null)
            {
                preset = new Preset(importer);
                AssetDatabase.CreateAsset(preset, PresetPath);
            }
            else
            {
                preset.UpdateProperties(importer);
            }
            var type = preset.GetPresetType();
            var defaults = Preset.GetDefaultPresetsForType(type).Where(d => d.preset != preset).ToList();
            defaults.Insert(0, new DefaultPreset("glob:\"Assets/Art/**\"", preset));
            Preset.SetDefaultPresetsForType(type, defaults.ToArray());

            foreach (var path in AssetDatabase.FindAssets("t:Texture2D", new[] { ArtRoot }).Select(AssetDatabase.GUIDToAssetPath))
            {
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                preset.ApplyTo(ti);
                ti.SaveAndReimport();
            }
        }

        static void ConfigurePixelSprite(TextureImporter ti)
        {
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.spritePixelsPerUnit = PixelsPerUnit;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.wrapMode = TextureWrapMode.Clamp;
            ti.npotScale = TextureImporterNPOTScale.None;
            var settings = new TextureImporterSettings();
            ti.ReadTextureSettings(settings);
            settings.spriteMeshType = SpriteMeshType.FullRect;
            ti.SetTextureSettings(settings);
            ti.SaveAndReimport();
        }

        static void UrpForPixels()
        {
            // Unity 6 assigns the pipeline per quality level; the Graphics default may be empty
            var assets = Enumerable.Range(0, QualitySettings.names.Length)
                .Select(QualitySettings.GetRenderPipelineAssetAt)
                .Append(GraphicsSettings.defaultRenderPipeline)
                .OfType<UniversalRenderPipelineAsset>().Distinct().ToList();
            if (assets.Count == 0)
                Debug.LogWarning("[PixelProjectSetup] No URP asset found in Graphics or Quality settings.");
            foreach (var urp in assets)
            {
                urp.msaaSampleCount = 1;   // MSAA off: hard pixel edges
                urp.renderScale = 1f;
                urp.supportsHDR = true;    // bloom on lanterns
                EditorUtility.SetDirty(urp);
            }
        }

        static void BuildLookTestScene()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            camGo.transform.position = new Vector3(0f, 0f, -10f);
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = RefHeight / 2f / PixelsPerUnit;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.05f, 0.06f, 0.12f);
            camGo.AddComponent<UniversalAdditionalCameraData>().renderPostProcessing = true;
            var ppc = camGo.AddComponent<PixelPerfectCamera>();
            ppc.assetsPPU = PixelsPerUnit;
            ppc.refResolutionX = RefWidth;
            ppc.refResolutionY = RefHeight;
            ppc.gridSnapping = PixelPerfectCamera.GridSnapping.UpscaleRenderTexture;
            ppc.cropFrame = PixelPerfectCamera.CropFrame.None;

            var global = new GameObject("Global Light 2D").AddComponent<Light2D>();
            global.lightType = Light2D.LightType.Global;
            global.color = new Color(0.82f, 0.86f, 1f);
            global.intensity = 0.85f;

            // two warm lanterns by the palace eaves (art pixels converted to world units)
            foreach (var (name, x, y) in new[] { ("Lantern Left", 150, 165), ("Lantern Right", 305, 165) })
            {
                var lamp = new GameObject(name).AddComponent<Light2D>();
                lamp.lightType = Light2D.LightType.Point;
                lamp.transform.position = ArtToWorld(x, y);
                lamp.color = new Color(1f, 0.66f, 0.36f);
                lamp.intensity = 1.1f;
                lamp.pointLightInnerRadius = 0.4f;
                lamp.pointLightOuterRadius = 3.2f;
            }

            var layers = new GameObject("Menu layers (look test)").transform;
            foreach (var (file, order) in LookTestLayers)
            {
                var sprite = AssetDatabase.LoadAssetAtPath<Sprite>($"{LookTestArt}/{file}.png");
                if (sprite == null)
                {
                    Debug.LogWarning($"[PixelProjectSetup] Missing sprite {file}.png");
                    continue;
                }
                var go = new GameObject(file);
                go.transform.SetParent(layers, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = sprite;
                sr.sortingOrder = order;
            }

            EditorSceneManager.SaveScene(scene, LookTestScene);
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>("Assets/Scenes/SampleScene.unity") != null)
                AssetDatabase.DeleteAsset("Assets/Scenes/SampleScene.unity");
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(LookTestScene, true) };
        }

        /// <summary>Art pixel (x right, y down from the top-left of the 480x270 frame) to world units.</summary>
        public static Vector3 ArtToWorld(float x, float y) =>
            new Vector3((x - RefWidth / 2f) / PixelsPerUnit, (RefHeight / 2f - y) / PixelsPerUnit, 0f);

        static void RenderLookTest(string outPath)
        {
            EditorSceneManager.OpenScene(LookTestScene);
            var cam = Camera.main;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            cam.Render();
            RenderTexture.active = rt;
            var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            tex.Apply();
            File.WriteAllBytes(outPath, tex.EncodeToPNG());
            cam.targetTexture = null;
            RenderTexture.active = null;
            UnityEngine.Object.DestroyImmediate(rt);
            Debug.Log($"[PixelProjectSetup] Rendered the look test to {outPath}");
        }
    }
}

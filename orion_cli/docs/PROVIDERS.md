# Orion CLI - LLM Provider Guide

Orion CLI supports 4 different LLM providers, giving you maximum flexibility between local models (100% offline) and cloud APIs.

---

## 🎯 Quick Comparison

| Provider | Type | Privacy | Cost | Required Configuration |
|----------|------|---------|------|------------------------|
| **Ollama** | Local | 🔒 100% private | Free | Ollama installed + models |
| **LM Studio** | Local | 🔒 100% private | Free | LM Studio + models |
| **OpenAI** | Cloud | ⚠️ Data sent to OpenAI | Paid (usage-based) | OpenAI API key |
| **Anthropic** | Cloud | ⚠️ Data sent to Anthropic | Paid (usage-based) | Anthropic API key |

---

## 1️⃣ Ollama (Recommended for Local Use)

**Advantages:**
- 100% private and offline
- Free
- Easy to install
- Large model catalog

**Installation:**
```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull qwen2.5-coder:7b
```

**Configuration in Orion:**
```
# Quick method (recommended)
> /provider ollama

# Or manually
> /settings set llm_provider ollama
> /settings set model qwen2.5-coder:7b
> /provider test
```

**Recommended Models:**
- `qwen2.5-coder:7b` - Excellent for code (recommended)
- `qwen2.5-coder:14b` - More powerful (requires more RAM)
- `deepseek-r1:7b` - Reasoning model (with `<think>`)
- `mistral:7b` - Good general purpose
- `llama3.3:latest` - Very powerful

---

## 2️⃣ LM Studio (Local Alternative)

**Advantages:**
- 100% private and offline
- User-friendly GUI
- Supports many model formats (GGUF, etc.)

> **⚠️ IMPORTANT:** LM Studio requires manual model loading!  
> Unlike Ollama, LM Studio does NOT automatically load models via API.  
> **Before using Orion**, you MUST:  
> 1. Open the LM Studio interface  
> 2. Go to "Developer" or "Local Server" tab  
> 3. Manually load your desired model (e.g., `meta-llama-3-8b-instruct`)  
> 4. Wait for 100% loading completion  
>   
> If no model is loaded, LM Studio will default to the first model alphabetically, which may not be the one configured in Orion.

**Installation:**
1. Download from https://lmstudio.ai
2. Launch LM Studio and load a model
3. Start the local server ("Server" tab, default: http://localhost:1234)

**Configuration in Orion:**

```
# Quick method (recommended) - interactive configuration
> /provider lmstudio
# Orion will ask for the URL and API key (optional)
```

Manual configuration:
```
> /settings set llm_provider lmstudio
> /settings set lmstudio_base_url http://localhost:1234/v1
> /settings set lmstudio_api_key lm-studio
> /provider test
```

---

## 3️⃣ OpenAI (Cloud)

**Advantages:**
- Very powerful models (GPT-4, GPT-4o)
- Reasoning models (o1-preview, o1-mini)
- No local GPU required

**Disadvantages:**
- Paid (usage-based pricing)
- Data sent to OpenAI
- Requires internet connection

**Configuration:**

1. Create an API key at https://platform.openai.com/api-keys

2. In Orion (quick method):
```
# Interactive configuration - recommended
> /provider openai
# Orion will ask for your API key and model
```

Manual configuration:
```
> /settings set llm_provider openai
> /settings set openai_api_key sk-proj-...
> /settings set model gpt-4o
> /provider test
```

**Recommended Models:**

| Model | Use Case | Relative Cost |
|-------|----------|---------------|
| `gpt-4o` | Most recent and powerful | Medium |
| `gpt-4o-mini` | Best price/performance ratio | Low |
| `gpt-4-turbo` | Powerful for complex tasks | High |
| `gpt-4` | Stable and reliable | High |
| `o1-preview` | Advanced reasoning | Very High |
| `o1-mini` | Fast reasoning | Medium |

**Pricing (approximate):**
- GPT-4o: ~$2.50/1M input tokens, ~$10/1M output tokens
- GPT-4o-mini: ~$0.15/1M input tokens, ~$0.60/1M output tokens
- o1-preview: ~$15/1M input tokens, ~$60/1M output tokens

More info: https://openai.com/api/pricing/

---

## 4️⃣ Anthropic (Claude)

**Advantages:**
- Very powerful models (Claude 3.5)
- Excellent for code and reasoning
- Large context window (200k tokens)
- No local GPU required

**Disadvantages:**
- Paid (usage-based pricing)
- Data sent to Anthropic
- Requires internet connection

**Configuration:**

1. Create an API key at https://console.anthropic.com/

2. In Orion (quick method):
```
# Interactive configuration - recommended
> /provider anthropic
# Orion will ask for your API key and model
```

Manual configuration:
```
> /settings set llm_provider anthropic
> /settings set anthropic_api_key sk-ant-...
> /settings set model claude-3-5-sonnet-20241022
> /provider test
```

**Recommended Models:**

| Model | Use Case | Relative Cost |
|-------|----------|---------------|
| `claude-3-5-sonnet-20241022` | Most powerful (recommended) | Medium |
| `claude-3-5-haiku-20241022` | Fast and economical | Low |
| `claude-3-opus-20240229` | Maximum capability | High |
| `claude-3-sonnet-20240229` | Performance/cost balance | Medium |
| `claude-3-haiku-20240307` | Fast for simple tasks | Low |

**Pricing (approximate):**
- Claude 3.5 Sonnet: ~$3/1M input tokens, ~$15/1M output tokens
- Claude 3.5 Haiku: ~$0.80/1M input tokens, ~$4/1M output tokens
- Claude 3 Opus: ~$15/1M input tokens, ~$75/1M output tokens

More info: https://www.anthropic.com/pricing

---

## 🔄 Switching Providers

You can switch providers at any time with the `/provider` command:

```
# View available providers
> /provider

# Switch provider (interactive configuration)
> /provider ollama
> /provider lmstudio
> /provider openai      # Will ask for your API key
> /provider anthropic   # Will ask for your API key

# Test connection to current provider
> /provider test
```

---

## 🔧 Changing Models

After selecting a provider, use `/model` to change models:

```
# View available models for current provider
> /model

# Change model by name
> /model qwen2.5-7b-instruct

# Change model by number (from detected list)
> /model 2
```

For **Ollama** and **LM Studio**, Orion will auto-detect available models on your system.

For **OpenAI** and **Anthropic**, Orion will show common model options.

---

## 💡 Best Practices

### For Local Development (Ollama/LM Studio)
- Use 7B models for faster responses on consumer hardware
- Use 14B+ models if you have 16GB+ RAM and a decent GPU
- Enable streaming mode for better UX: `/streaming`

### For Cloud APIs (OpenAI/Anthropic)
- Use mini/haiku models for simple tasks to save costs
- Use full/sonnet models for complex reasoning
- Monitor your API usage on provider dashboards
- Set spending limits on your API accounts

### General Tips
- Test connection after configuration: `/provider test`
- Save API keys to settings (encrypted storage coming soon)
- Use `/model` to quickly switch between models
- Check `/stats` to monitor token usage

---

## 🔒 Security Notes

**API Keys:**
- Stored in `~/.config/orion/settings.json` (local file)
- Never committed to git (add to .gitignore)
- Consider using environment variables for CI/CD: `ORION_OPENAI_API_KEY`, `ORION_ANTHROPIC_API_KEY`

**Local Models:**
- No API keys needed
- Zero external data transmission
- Full privacy and control

---

## 🆘 Troubleshooting

### Ollama not connecting
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### LM Studio not connecting
```bash
# Check if LM Studio server is running
curl http://localhost:1234/v1/models

# In LM Studio: Server tab → Start Server
```

### OpenAI API errors
- Verify API key is valid: https://platform.openai.com/api-keys
- Check account balance: https://platform.openai.com/account/billing
- Ensure model name is correct (case-sensitive)

### Anthropic API errors
- Verify API key is valid: https://console.anthropic.com/
- Check account balance
- Ensure model name is correct (case-sensitive)

---

## 📚 Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/README.md)
- [LM Studio Guides](https://lmstudio.ai/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Reference](https://docs.anthropic.com/claude/reference)

---

**Need help?** Open an issue on [GitHub](https://github.com/yourusername/project_orion/issues)
# Orion CLI - Guide des Providers LLM

Orion CLI supporte 4 providers LLM différents, vous donnant une flexibilité maximale entre modèles locaux (100% offline) et APIs cloud.

---

## 🎯 Comparaison rapide

| Provider | Type | Confidentialité | Coût | Configuration requise |
|----------|------|-----------------|------|----------------------|
| **Ollama** | Local | 🔒 100% privé | Gratuit | Ollama installé + modèles |
| **LM Studio** | Local | 🔒 100% privé | Gratuit | LM Studio + modèles |
| **OpenAI** | Cloud | ⚠️ Données envoyées à OpenAI | Payant (usage) | Clé API OpenAI |
| **Anthropic** | Cloud | ⚠️ Données envoyées à Anthropic | Payant (usage) | Clé API Anthropic |

---

## 1️⃣ Ollama (Recommandé pour usage local)

**Avantages:**
- 100% privé et offline
- Gratuit
- Facile à installer
- Large catalogue de modèles

**Installation:**
```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Télécharger un modèle
ollama pull qwen2.5-coder:7b
```

**Configuration dans Orion:**
```
# Méthode rapide (recommandée)
> /provider ollama

# Ou manuellement
> /settings set llm_provider ollama
> /settings set model qwen2.5-coder:7b
> /settings test-provider
```

**Modèles recommandés:**
- `qwen2.5-coder:7b` - Excellent pour le code (recommandé)
- `qwen2.5-coder:14b` - Plus puissant (nécessite plus de RAM)
- `deepseek-r1:7b` - Modèle de raisonnement (avec `<think>`)
- `mistral:7b` - Bon généraliste
- `llama3.3:latest` - Très performant

---

## 2️⃣ LM Studio (Alternative locale)

**Avantages:**
- 100% privé et offline
- Interface graphique conviviale
- Support de nombreux formats de modèles (GGUF, etc.)

**Installation:**
1. Télécharger depuis https://lmstudio.ai
2. Lancer LM Studio et charger un modèle
3. Démarrer le serveur local (onglet "Server", défaut: http://localhost:1234)
# Méthode rapide (recommandée) - configuration interactive
> /provider lmstudio
# Orion vous demandera l'URL et la clé API (optionnelle)

# Ou configuration manuelle
> /settings set llm_provider lmstudio

Configuration manuelle:
```
> /settings set lmstudio_base_url http://localhost:1234/v1
> /settings set lmstudio_api_key lm-studio
> /settings test-provider
```

---

## 3️⃣ OpenAI (Cloud)

**Avantages:**
- Modèles très puissants (GPT-4, GPT-4o)
- Modèles de raisonnement (o1-preview, o1-mini)
- Pas besoin de GPU local

**Inconvénients:**
- Payant (tarification à l'usage)
- Données envoyées à OpenAI
- Nécessite une connexion internet

**Configuration:**

1. Créer une clé API sur https://platform.openai.com/api-keys

2. Dans Orion (méthode rapide):
```
# Configuration interactive - recommandée
> /provider openai
# Orion vous demandera votre clé API et le modèle
```

Configuration manuelle:
```
> /settings set llm_provider openai
> /settings set openai_api_key sk-proj-...
> /settings set model gpt-4o
> /settings test-provider
```

**Modèles recommandés:**

| Modèle | Usage | Coût relatif |
|--------|-------|--------------|
| `gpt-4o` | Le plus récent et performant | Moyen |
| `gpt-4o-mini` | Bon rapport qualité/prix | Bas |
| `gpt-4-turbo` | Puissant pour tâches complexes | Élevé |
| `gpt-4` | Stable et fiable | Élevé |
| `o1-preview` | Raisonnement avancé | Très élevé |
| `o1-mini` | Raisonnement rapide | Moyen |

**Tarification (approximative):**
- GPT-4o: ~$2.50/1M tokens input, ~$10/1M tokens output
- GPT-4o-mini: ~$0.15/1M tokens input, ~$0.60/1M tokens output
- o1-preview: ~$15/1M tokens input, ~$60/1M tokens output

Plus d'infos: https://openai.com/api/pricing/

---

## 4️⃣ Anthropic (Claude)

**Avantages:**
- Modèles très performants (Claude 3.5)
- Excellents pour le code et le raisonnement
- Fenêtre de contexte large (200k tokens)
- Pas besoin de GPU local

**Inconvénients:**
- Payant (tarification à l'usage)
- Données envoyées à Anthropic
- Nécessite une connexion internet

**Configuration:**

1. Créer une  (méthode rapide):
```
# Configuration interactive - recommandée
> /provider anthropic
# Orion vous demandera votre clé API et le modèle
```

Configuration manuelle:
```
> /settings set llm_provider anthropic
Configuration manuelle:
```
> /settings set anthropic_api_key sk-ant-...
> /settings set model claude-3-5-sonnet-20241022
> /settings test-provider
```

**Modèles recommandés:**

| Modèle | Usage | Coût relatif |
|--------|-------|--------------|
| `claude-3-5-sonnet-20241022` | Le plus performant (recommandé) | Moyen |
| `claude-3-5-haiku-20241022` | Rapide et économique | Bas |
| `claude-3-opus-20240229` | Maximum de capacité | Élevé |
| `claude-3-sonnet-20240229` | Équilibre perf/coût | Moyen |
| `claude-3-haiku-20240307` | Rapide pour tâches simples | Bas |

**Tarification (approximative):**
- Claude 3.5 Sonnet: ~$3/1M tokens input, ~$15/1M tokens output
- Claude 3.5 Haiku: ~$0.80/1M tokens input, ~$4/1M tokens output
- Claude 3 Opus: ~$15/1M tokens input, ~$75/1M tokens output

Plus d'infos: https://www.anthropic.com/pricing

---

## 🔄 Changer de provider

Vous pouvez changer de provider à tout moment avec la commande `/provider` :

```
# Voir les providers disponibles
> /provider

# Changer de provider (configuration interactive)
> /provider ollama
> /provider lmstudio
> /provider openai      # Vous demandera votre API key
> /provider anthropic   # Vous demandera votre API key

# Tester la connexion au provider actuel
> /provider test
```

**Alternative (configuration manuelle):**
```
> /settings set llm_provider ollama|lmstudio|openai|anthropic
```

Le changement prend effet immédiatement (votre historique de conversation est conservé).

---

## 🧪 Tester la connexion
# Via la commande /provider
> /provider test

# Ou via /settings

Après configuration, testez toujours la connexion :

```
> /settings test-provider
```

Cela vérifiera :
- ✅ Que le provider est accessible
- ✅ Que vos identifiants sont valides
- ✅ Que le modèle sélectionné est disponible

---

## 💡 Recommandations

**Pour usage personnel/privé:**
- Utilisez **Ollama** (gratuit, privé, performant)
- Alternative: **LM Studio** si vous préférez une interface graphique

**Pour usage professionnel/production:**
- **Claude 3.5 Sonnet** (meilleur équilibre performance/coût)
- **GPT-4o** si vous êtes déjà dans l'écosystème OpenAI

**Pour expérimentation:**
- Commencez avec **Ollama** (gratuit)
- Testez **GPT-4o-mini** ou **Claude 3.5 Haiku** pour comparer (coût faible)

---

## 🔒 Sécurité des API Keys

- Les clés API sont stockées dans `~/.config/orion/settings.json`
- Permissions du fichier: lisible uniquement par votre utilisateur (600)
- Les clés sont masquées dans `/settings` (affiche seulement les 4 derniers caractères)
- **Ne committez JAMAIS votre settings.json dans Git**

Ajoutez dans votre `.gitignore`:
```
.orion/settings.json
~/.config/orion/settings.json
```

---

## 📊 Comparaison de performance

| Tâche | Ollama (local) | LM Studio (local) | OpenAI GPT-4o | Claude 3.5 Sonnet |
|-------|----------------|-------------------|---------------|-------------------|
| Code simple | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Code complexe | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Raisonnement | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Vitesse | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Confidentialité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |
| Coût | ⭐⭐⭐⭐⭐ (gratuit) | ⭐⭐⭐⭐⭐ (gratuit) | ⭐⭐⭐ | ⭐⭐⭐ |

---

## ❓ FAQ

**Q: Puis-je utiliser plusieurs providers simultanément?**
A: Non, un seul provider actif à la fois. Mais vous pouvez changer facilement avec `/settings set llm_provider`.

**Q: Mes conversations sont-elles conservées quand je change de provider?**
A: Oui, l'historique est indépendant du provider.

**Q: Quel provider consomme le moins de ressources?**
A: LM Studio et Ollama sont locaux (utilisent votre GPU/CPU). OpenAI et Anthropic n'utilisent que votre connexion internet.

**Q: Puis-je utiliser mon propre serveur OpenAI-compatible?**
A: Oui, utilisez `lmstudio` et configurez l'URL avec `/settings set lmstudio_base_url`.

**Q: Comment obtenir des crédits gratuits OpenAI/Anthropic?**
A: Les nouveaux comptes OpenAI reçoivent parfois des crédits gratuits. Anthropic offre des crédits d'essai sur demande.
